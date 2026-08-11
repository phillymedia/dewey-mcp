"""Azure AI Search provider adapter for the Image Archive."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from time import monotonic
from typing import Any

import backoff
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError, HttpResponseError
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery

from dewey_mcp.errors import SearchProviderError, SearchProviderTimeoutError
from dewey_mcp.filters import AzureFilterFieldNames, build_azure_filter
from dewey_mcp.models import (
    ImageSearchRequest,
    ImageSearchResponse,
    ImageSearchResult,
)
from dewey_mcp.settings import Settings

LOGGER = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


@dataclass(frozen=True)
class AzureImageIndexFieldMapping:
    """Azure image-index field names used by the provider adapter."""

    id: str
    image_url: str
    thumbnail_url: str
    screen_url: str
    authors: str
    caption: str
    description: str
    description_vector: str
    created_date: str
    captured_date: str

    @property
    def filter_field_names(self) -> AzureFilterFieldNames:
        return AzureFilterFieldNames(
            publish_date=self.captured_date,
            authors=self.authors,
        )

    @property
    def keyword_fields(self) -> list[str]:
        return [self.authors, self.caption, self.description]

    @property
    def select_fields(self) -> list[str]:
        return [
            self.id,
            self.image_url,
            self.thumbnail_url,
            self.screen_url,
            self.authors,
            self.caption,
            self.description,
            self.created_date,
            self.captured_date,
        ]


DEFAULT_AZURE_IMAGE_INDEX_FIELD_MAPPING = AzureImageIndexFieldMapping(
    id="id",
    image_url="image_url",
    thumbnail_url="thumbnail_url",
    screen_url="screen_url",
    authors="authors",
    caption="caption",
    description="description",
    description_vector="description_vector",
    created_date="created_date",
    captured_date="captured_date",
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
                    "filter_fields": _request_filter_fields(request),
                    "requested_limit": request.limit,
                    "provider_latency_ms": round(
                        (monotonic() - started) * 1000,
                        2,
                    ),
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
            "search_fields": self.field_mapping.keyword_fields,
            "filter": filter_expression,
            "top": request.limit,
            "select": self.field_mapping.select_fields,
        }
        if vector_queries:
            search_kwargs["vector_queries"] = vector_queries

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
                fields=self.field_mapping.description_vector,
            )
        ]

    def _map_result(self, document: dict[str, Any]) -> ImageSearchResult:
        return ImageSearchResult(
            id=document[self.field_mapping.id],
            image_url=document.get(self.field_mapping.image_url),
            thumbnail_url=document.get(self.field_mapping.thumbnail_url),
            screen_url=document.get(self.field_mapping.screen_url),
            authors=document.get(self.field_mapping.authors),
            caption=document.get(self.field_mapping.caption),
            description=document.get(self.field_mapping.description),
            created_date=document.get(self.field_mapping.created_date),
            captured_date=document.get(self.field_mapping.captured_date),
        )


def _request_filter_fields(request: ImageSearchRequest) -> list[str]:
    fields: list[str] = []
    if request.start_date is not None or request.end_date is not None:
        fields.append("captured_date")
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
