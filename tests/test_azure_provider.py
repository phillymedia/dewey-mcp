from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest

from dewey_mcp.models import ImageSearchRequest, SearchRequest
from dewey_mcp.providers.azure import (
    AzureArchiveSearchProvider,
    AzureImageIndexFieldMapping,
    AzureImageSearchProvider,
    AzureIndexFieldMapping,
)
from dewey_mcp.settings import Settings


class FakeAsyncResults:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self._results = results

    async def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        for item in self._results:
            yield item


class FakeSearchClient:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.last_kwargs: dict[str, Any] | None = None

    async def search(self, **kwargs: Any) -> FakeAsyncResults:
        self.last_kwargs = kwargs
        return FakeAsyncResults(self.results)

    async def get_document_count(self) -> int:
        return 1

    async def close(self) -> None:
        return None


def make_settings() -> Settings:
    return Settings(
        azure_search_endpoint="https://example.search.windows.net",
        azure_search_index_name="archive",
        azure_search_semantic_configuration="semantic",
        azure_image_search_index_name="images",
        azure_image_search_semantic_configuration="image-semantic",
        azure_search_api_key="secret",
    )


def test_settings_do_not_define_azure_index_field_env_mapping() -> None:
    assert "azure_search_field_title" not in Settings.model_fields
    assert not hasattr(
        make_settings(),
        "azure_search_field_title",
    )


def test_settings_define_image_index_without_field_env_mapping() -> None:
    assert "azure_image_search_index_name" in Settings.model_fields
    assert "azure_image_search_semantic_configuration" in Settings.model_fields
    assert "azure_image_search_field_description" not in Settings.model_fields


@pytest.mark.asyncio
async def test_azure_provider_maps_index_fields_to_result_contract() -> None:
    fake_client = FakeSearchClient(
        [
            {
                "chunk_id": "chunk-1",
                "parent_id": "article-1",
                "headline": "Hostage crisis",
                "publish_date": datetime(1979, 11, 15, tzinfo=UTC),
                "authors": "Jane Reporter",
                "link": "https://example.test/article-1",
                "chunk": "Article chunk text",
                "@search.score": 3.5,
            }
        ]
    )
    provider = AzureArchiveSearchProvider(
        settings=make_settings(),
        search_client=fake_client,
    )

    response = await provider.search(SearchRequest(query="hostage"))

    assert response.count == 1
    assert response.results[0].model_dump() == {
        "chunk_id": "chunk-1",
        "article_id": "article-1",
        "title": "Hostage crisis",
        "published_date": datetime(1979, 11, 15, tzinfo=UTC),
        "author": "Jane Reporter",
        "link": "https://example.test/article-1",
        "chunk_text": "Article chunk text",
        "score": 3.5,
    }


@pytest.mark.asyncio
async def test_azure_provider_can_use_explicit_index_field_mapping() -> None:
    field_mapping = AzureIndexFieldMapping(
        chunk_id="archive_chunk_id",
        chunk_text="body_chunk",
        title="title",
        vector="body_vector",
        link="url",
        author="byline",
        published_date="published_at",
        article_id="archive_article_id",
    )
    fake_client = FakeSearchClient(
        [
            {
                "archive_chunk_id": "chunk-1",
                "archive_article_id": "article-1",
                "title": "Hostage crisis",
                "published_at": datetime(1979, 11, 15, tzinfo=UTC),
                "byline": "Jane Reporter",
                "url": "https://example.test/article-1",
                "body_chunk": "Article chunk text",
            }
        ]
    )
    provider = AzureArchiveSearchProvider(
        settings=make_settings(),
        search_client=fake_client,
        field_mapping=field_mapping,
    )

    response = await provider.search(SearchRequest(query="hostage"))

    assert fake_client.last_kwargs is not None
    assert fake_client.last_kwargs["select"] == [
        "archive_chunk_id",
        "archive_article_id",
        "title",
        "published_at",
        "byline",
        "url",
        "body_chunk",
    ]
    assert fake_client.last_kwargs["vector_queries"][0].fields == "body_vector"
    assert response.results[0].article_id == "article-1"
    assert response.results[0].chunk_text == "Article chunk text"


@pytest.mark.asyncio
async def test_azure_provider_uses_hybrid_search_for_normal_search_text() -> None:
    fake_client = FakeSearchClient([])
    provider = AzureArchiveSearchProvider(
        settings=make_settings(),
        search_client=fake_client,
    )

    await provider.search(SearchRequest(query="hostage", limit=5))

    assert fake_client.last_kwargs is not None
    assert fake_client.last_kwargs["search_text"] == "hostage"
    assert fake_client.last_kwargs["top"] == 5
    assert fake_client.last_kwargs["query_type"] is not None
    assert fake_client.last_kwargs["semantic_configuration_name"] == "semantic"
    assert len(fake_client.last_kwargs["vector_queries"]) == 1


@pytest.mark.asyncio
async def test_azure_provider_omits_vector_query_for_search_everything() -> None:
    fake_client = FakeSearchClient([])
    provider = AzureArchiveSearchProvider(
        settings=make_settings(),
        search_client=fake_client,
    )

    await provider.search(SearchRequest(query="*"))

    assert fake_client.last_kwargs is not None
    assert fake_client.last_kwargs["search_text"] == "*"
    assert "vector_queries" not in fake_client.last_kwargs
    assert "query_type" not in fake_client.last_kwargs


@pytest.mark.asyncio
async def test_azure_image_provider_maps_index_fields_to_result_contract() -> None:
    fake_client = FakeSearchClient(
        [
            {
                "image_id": "image-1",
                "image_url": "https://example.test/image-1.jpg",
                "caption": "Ribbon cutting",
                "description": "Officials cut a ribbon at city hall.",
                "authors": "Photo Staff",
                "capture_date": datetime(2024, 5, 1, tzinfo=UTC),
                "@search.score": 2.5,
            }
        ]
    )
    provider = AzureImageSearchProvider(
        settings=make_settings(),
        search_client=fake_client,
    )

    response = await provider.search(ImageSearchRequest(query="ribbon"))

    assert response.count == 1
    assert response.results[0].model_dump() == {
        "image_id": "image-1",
        "image_url": "https://example.test/image-1.jpg",
        "caption": "Ribbon cutting",
        "description": "Officials cut a ribbon at city hall.",
        "authors": "Photo Staff",
        "capture_date": datetime(2024, 5, 1, tzinfo=UTC),
        "score": 2.5,
    }


@pytest.mark.asyncio
async def test_azure_image_provider_can_use_explicit_index_field_mapping() -> None:
    field_mapping = AzureImageIndexFieldMapping(
        image_id="asset_id",
        image_url="url",
        caption="title",
        description="alt_text",
        authors="credit",
        capture_date="captured_at",
        vector="alt_text_vector",
    )
    fake_client = FakeSearchClient(
        [
            {
                "asset_id": "image-1",
                "url": "https://example.test/image-1.jpg",
                "title": "Ribbon cutting",
                "alt_text": "Officials cut a ribbon at city hall.",
                "credit": "Photo Staff",
                "captured_at": datetime(2024, 5, 1, tzinfo=UTC),
            }
        ]
    )
    provider = AzureImageSearchProvider(
        settings=make_settings(),
        search_client=fake_client,
        field_mapping=field_mapping,
    )

    response = await provider.search(ImageSearchRequest(query="ribbon"))

    assert fake_client.last_kwargs is not None
    assert fake_client.last_kwargs["select"] == [
        "asset_id",
        "url",
        "title",
        "alt_text",
        "credit",
        "captured_at",
    ]
    assert fake_client.last_kwargs["search_fields"] == ["alt_text"]
    assert fake_client.last_kwargs["vector_queries"][0].fields == "alt_text_vector"
    assert response.results[0].image_id == "image-1"
    assert response.results[0].description == "Officials cut a ribbon at city hall."


@pytest.mark.asyncio
async def test_azure_image_provider_uses_hybrid_search_for_normal_search_text() -> None:
    fake_client = FakeSearchClient([])
    provider = AzureImageSearchProvider(
        settings=make_settings(),
        search_client=fake_client,
    )

    await provider.search(ImageSearchRequest(query="ribbon", limit=5))

    assert fake_client.last_kwargs is not None
    assert fake_client.last_kwargs["search_text"] == "ribbon"
    assert fake_client.last_kwargs["search_fields"] == ["description"]
    assert fake_client.last_kwargs["top"] == 5
    assert fake_client.last_kwargs["query_type"] is not None
    assert fake_client.last_kwargs["semantic_configuration_name"] == "image-semantic"
    assert fake_client.last_kwargs["vector_queries"][0].fields == "description_vector"


@pytest.mark.asyncio
async def test_azure_image_provider_omits_vector_query_for_search_everything() -> None:
    fake_client = FakeSearchClient([])
    provider = AzureImageSearchProvider(
        settings=make_settings(),
        search_client=fake_client,
    )

    await provider.search(ImageSearchRequest(query="*"))

    assert fake_client.last_kwargs is not None
    assert fake_client.last_kwargs["search_text"] == "*"
    assert "vector_queries" not in fake_client.last_kwargs
    assert "query_type" not in fake_client.last_kwargs
