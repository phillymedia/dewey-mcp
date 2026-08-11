from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest

from dewey_mcp.models import SearchRequest
from dewey_mcp.providers.azure import AzureArchiveSearchProvider, AzureIndexFieldMapping
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
        azure_image_search_index_name="inq-betadam-images",
        azure_search_semantic_configuration="semantic",
        azure_search_api_key="secret",
    )


def test_settings_do_not_define_azure_index_field_env_mapping() -> None:
    assert "azure_search_field_title" not in Settings.model_fields
    assert not hasattr(
        make_settings(),
        "azure_search_field_title",
    )


@pytest.mark.asyncio
async def test_azure_provider_maps_index_fields_to_result_contract() -> None:
    fake_client = FakeSearchClient(
        [
            {
                "sourcepage": "articles/article-1.pdf",
                "headline": "Hostage crisis",
                "publish_date": datetime(1979, 11, 15, tzinfo=UTC),
                "authors": "Jane Reporter",
                "link": "https://example.test/article-1",
                "chunk": "Article chunk text",
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
        "source_id": "doc_article-1",
        "text": "Article chunk text",
        "title": "Hostage crisis",
        "published_date": datetime(1979, 11, 15, tzinfo=UTC),
        "author": "Jane Reporter",
        "url": "https://example.test/article-1",
    }


@pytest.mark.asyncio
async def test_azure_provider_can_use_explicit_index_field_mapping() -> None:
    field_mapping = AzureIndexFieldMapping(
        chunk_text="body_chunk",
        sourcepage="source_page",
        title="title",
        vector="body_vector",
        link="url",
        author="byline",
        published_date="published_at",
    )
    fake_client = FakeSearchClient(
        [
            {
                "source_page": "articles/article-1.pdf",
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
        "source_page",
        "title",
        "published_at",
        "byline",
        "url",
        "body_chunk",
    ]
    assert fake_client.last_kwargs["vector_queries"][0].fields == "body_vector"
    assert response.results[0].source_id == "doc_article-1"
    assert response.results[0].text == "Article chunk text"


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
