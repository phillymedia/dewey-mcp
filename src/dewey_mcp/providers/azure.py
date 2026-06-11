"""Azure AI Search provider adapter."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import suppress
from dataclasses import dataclass
from time import monotonic
from typing import Any

import backoff
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, HttpResponseError
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import QueryType, VectorizableTextQuery

from dewey_mcp.errors import SearchProviderError, SearchProviderTimeoutError
from dewey_mcp.filters import AzureFilterFieldNames, build_azure_filter
from dewey_mcp.models import (
    ImageSearchRequest,
    ImageSearchResponse,
    ImageSearchResult,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from dewey_mcp.settings import Settings

LOGGER = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


@dataclass(frozen=True)
class AzureIndexFieldMapping:
    """Azure index field names used by the provider adapter."""

    chunk_id: str
    chunk_text: str
    title: str
    vector: str
    link: str
    author: str
    published_date: str
    article_id: str

    @property
    def filter_field_names(self) -> AzureFilterFieldNames:
        return AzureFilterFieldNames(
            date=self.published_date,
            authors=self.author,
        )

    @property
    def select_fields(self) -> list[str]:
        return [
            self.chunk_id,
            self.article_id,
            self.title,
            self.published_date,
            self.author,
            self.link,
            self.chunk_text,
        ]


DEFAULT_AZURE_INDEX_FIELD_MAPPING = AzureIndexFieldMapping(
    chunk_id="chunk_id",
    chunk_text="chunk",
    title="headline",
    vector="text_vector",
    link="link",
    author="authors",
    published_date="publish_date",
    article_id="parent_id",
)


@dataclass(frozen=True)
class AzureImageIndexFieldMapping:
    """Azure image index field names used by the provider adapter."""

    image_id: str
    image_url: str
    caption: str
    description: str
    authors: str
    capture_date: str
    vector: str

    @property
    def filter_field_names(self) -> AzureFilterFieldNames:
        return AzureFilterFieldNames(
            date=self.capture_date,
            authors=self.authors,
        )

    @property
    def select_fields(self) -> list[str]:
        return [
            self.image_id,
            self.image_url,
            self.caption,
            self.description,
            self.authors,
            self.capture_date,
        ]


DEFAULT_AZURE_IMAGE_INDEX_FIELD_MAPPING = AzureImageIndexFieldMapping(
    image_id="image_id",
    image_url="image_url",
    caption="caption",
    description="description",
    authors="byline",
    capture_date="capture_date",
    vector="description_vector",
)


@dataclass
class AzureArchiveSearchProvider:
    """ArchiveSearchProvider implementation backed by Azure AI Search."""

    settings: Settings
    search_client: SearchClient
    credential: DefaultAzureCredential | None = None
    field_mapping: AzureIndexFieldMapping = DEFAULT_AZURE_INDEX_FIELD_MAPPING

    @classmethod
    def from_settings(cls, settings: Settings) -> AzureArchiveSearchProvider:
        credential: AzureKeyCredential | DefaultAzureCredential
        closeable_credential: DefaultAzureCredential | None = None

        if settings.azure_search_api_key is not None:
            credential = AzureKeyCredential(
                settings.azure_search_api_key.get_secret_value()
            )
        else:
            closeable_credential = DefaultAzureCredential()
            credential = closeable_credential

        search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=credential,
        )
        return cls(
            settings=settings,
            search_client=search_client,
            credential=closeable_credential,
        )

    async def search(self, request: SearchRequest) -> SearchResponse:
        started = monotonic()
        try:
            return await asyncio.wait_for(
                self._search_with_retries(request),
                timeout=self.settings.search_provider_timeout_seconds,
            )
        except TimeoutError as exc:
            raise SearchProviderTimeoutError() from exc
        except AzureError as exc:
            raise SearchProviderError() from exc
        finally:
            LOGGER.info(
                "azure_search_completed",
                extra={
                    "query_length": len(request.query),
                    "filter_fields": _request_filter_fields(request),
                    "requested_limit": request.limit,
                    "provider_latency_ms": round((monotonic() - started) * 1000, 2),
                },
            )

    async def probe(self) -> None:
        try:
            await asyncio.wait_for(
                self.search_client.get_document_count(),
                timeout=self.settings.search_provider_timeout_seconds,
            )
        except TimeoutError as exc:
            raise SearchProviderTimeoutError() from exc
        except AzureError as exc:
            raise SearchProviderError() from exc

    async def close(self) -> None:
        await self.search_client.close()
        if self.credential is not None:
            await self.credential.close()

    @backoff.on_exception(
        backoff.expo,
        AzureError,
        max_tries=3,
        jitter=backoff.full_jitter,
        giveup=lambda exc: not _is_retryable(exc),
    )
    async def _search_with_retries(self, request: SearchRequest) -> SearchResponse:
        results = await self._execute_search(request)
        return SearchResponse.from_results(results)

    async def _execute_search(self, request: SearchRequest) -> list[SearchResult]:
        filter_expression = build_azure_filter(
            request,
            self.field_mapping.filter_field_names,
        )
        vector_queries = self._build_vector_queries(request)

        search_kwargs: dict[str, Any] = {
            "search_text": request.query,
            "filter": filter_expression,
            "top": request.limit,
            "select": self.field_mapping.select_fields,
        }
        if vector_queries:
            search_kwargs["vector_queries"] = vector_queries
            search_kwargs["query_type"] = QueryType.SEMANTIC
            search_kwargs["semantic_configuration_name"] = (
                self.settings.azure_search_semantic_configuration
            )

        raw_results = await self.search_client.search(**search_kwargs)
        return [
            self._map_result(document)
            async for document in _take(raw_results, request.limit)
        ]

    def _build_vector_queries(
        self,
        request: SearchRequest,
    ) -> list[VectorizableTextQuery]:
        if request.query == "*":
            return []
        return [
            VectorizableTextQuery(
                text=request.query,
                k_nearest_neighbors=request.limit,
                fields=self.field_mapping.vector,
            )
        ]

    def _map_result(self, document: dict[str, Any]) -> SearchResult:
        return SearchResult(
            chunk_id=str(document[self.field_mapping.chunk_id]),
            article_id=str(document[self.field_mapping.article_id]),
            title=document.get(self.field_mapping.title),
            published_date=document.get(self.field_mapping.published_date),
            author=document.get(self.field_mapping.author),
            link=document.get(self.field_mapping.link),
            chunk_text=str(document[self.field_mapping.chunk_text]),
            score=float(document.get("@search.score") or 0.0),
        )


@dataclass
class AzureImageSearchProvider:
    """ImageSearchProvider implementation backed by Azure AI Search."""

    settings: Settings
    search_client: SearchClient
    credential: DefaultAzureCredential | None = None
    field_mapping: AzureImageIndexFieldMapping = DEFAULT_AZURE_IMAGE_INDEX_FIELD_MAPPING

    @classmethod
    def from_settings(cls, settings: Settings) -> AzureImageSearchProvider:
        credential: AzureKeyCredential | DefaultAzureCredential
        closeable_credential: DefaultAzureCredential | None = None

        if settings.azure_search_api_key is not None:
            credential = AzureKeyCredential(
                settings.azure_search_api_key.get_secret_value()
            )
        else:
            closeable_credential = DefaultAzureCredential()
            credential = closeable_credential

        search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_image_search_index_name,
            credential=credential,
        )
        return cls(
            settings=settings,
            search_client=search_client,
            credential=closeable_credential,
        )

    async def search(self, request: ImageSearchRequest) -> ImageSearchResponse:
        started = monotonic()
        try:
            return await asyncio.wait_for(
                self._search_with_retries(request),
                timeout=self.settings.search_provider_timeout_seconds,
            )
        except TimeoutError as exc:
            raise SearchProviderTimeoutError() from exc
        except AzureError as exc:
            raise SearchProviderError() from exc
        finally:
            LOGGER.info(
                "azure_image_search_completed",
                extra={
                    "query_length": len(request.query),
                    "filter_fields": _request_filter_fields(
                        request,
                        date_field="capture_date",
                    ),
                    "requested_limit": request.limit,
                    "provider_latency_ms": round((monotonic() - started) * 1000, 2),
                },
            )

    async def probe(self) -> None:
        try:
            await asyncio.wait_for(
                self.search_client.get_document_count(),
                timeout=self.settings.search_provider_timeout_seconds,
            )
        except TimeoutError as exc:
            raise SearchProviderTimeoutError() from exc
        except AzureError as exc:
            raise SearchProviderError() from exc

    async def close(self) -> None:
        await self.search_client.close()
        if self.credential is not None:
            await self.credential.close()

    @backoff.on_exception(
        backoff.expo,
        AzureError,
        max_tries=3,
        jitter=backoff.full_jitter,
        giveup=lambda exc: not _is_retryable(exc),
    )
    async def _search_with_retries(
        self,
        request: ImageSearchRequest,
    ) -> ImageSearchResponse:
        results = await self._execute_search(request)
        return ImageSearchResponse.from_results(results)

    async def _execute_search(
        self,
        request: ImageSearchRequest,
    ) -> list[ImageSearchResult]:
        filter_expression = build_azure_filter(
            request,
            self.field_mapping.filter_field_names,
        )
        vector_queries = self._build_vector_queries(request)

        search_kwargs: dict[str, Any] = {
            "search_text": request.query,
            "search_fields": [self.field_mapping.description],
            "filter": filter_expression,
            "top": request.limit,
            "select": self.field_mapping.select_fields,
        }
        if vector_queries:
            search_kwargs["vector_queries"] = vector_queries
            search_kwargs["query_type"] = QueryType.SEMANTIC
            search_kwargs["semantic_configuration_name"] = (
                self.settings.azure_image_search_semantic_configuration
            )

        raw_results = await self.search_client.search(**search_kwargs)
        return [
            self._map_result(document)
            async for document in _take(raw_results, request.limit)
        ]

    def _build_vector_queries(
        self,
        request: ImageSearchRequest,
    ) -> list[VectorizableTextQuery]:
        if request.query == "*":
            return []
        return [
            VectorizableTextQuery(
                text=request.query,
                k_nearest_neighbors=request.limit,
                fields=self.field_mapping.vector,
            )
        ]

    def _map_result(self, document: dict[str, Any]) -> ImageSearchResult:
        return ImageSearchResult(
            image_id=str(document[self.field_mapping.image_id]),
            image_url=document.get(self.field_mapping.image_url),
            caption=document.get(self.field_mapping.caption),
            description=str(document[self.field_mapping.description]),
            authors=document.get(self.field_mapping.authors),
            capture_date=document.get(self.field_mapping.capture_date),
            score=float(document.get("@search.score") or 0.0),
        )


def _request_filter_fields(
    request: SearchRequest | ImageSearchRequest,
    *,
    date_field: str = "published_date",
) -> list[str]:
    fields: list[str] = []
    if request.start_date is not None or request.end_date is not None:
        fields.append(date_field)
    if request.authors:
        fields.append("authors")
    return fields


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, HttpResponseError):
        return exc.status_code in _RETRYABLE_STATUS_CODES
    return isinstance(exc, AzureError)


async def _take(
    results: AsyncIterator[dict[str, Any]],
    limit: int,
) -> AsyncIterator[dict[str, Any]]:
    count = 0
    async for item in results:
        if count >= limit:
            break
        count += 1
        yield item


async def close_provider(provider: object) -> None:
    close = getattr(provider, "close", None)
    if close is not None:
        with suppress(Exception):
            await close()
