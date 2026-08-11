import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
from azure.core.exceptions import AzureError

from dewey_mcp.errors import SearchProviderError, SearchProviderTimeoutError
from dewey_mcp.models import ImageSearchRequest
from dewey_mcp.providers import azure_image
from dewey_mcp.providers.azure_image import (
    AzureImageIndexFieldMapping,
    AzureImageSearchProvider,
)
from dewey_mcp.settings import Settings


class FakeAsyncResults:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self._results = results

    async def __aiter__(self) -> AsyncIterator[dict[str, Any]]:
        for item in self._results:
            yield item


class FakeSearchClient:
    def __init__(self, outcomes: list[object] | None = None) -> None:
        self.outcomes = outcomes or [[]]
        self.search_calls: list[dict[str, Any]] = []
        self.probe_calls = 0
        self.closed = False

    async def search(self, **kwargs: Any) -> FakeAsyncResults:
        self.search_calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return FakeAsyncResults(outcome)

    async def get_document_count(self) -> int:
        self.probe_calls += 1
        return 1

    async def close(self) -> None:
        self.closed = True


class HangingSearchClient(FakeSearchClient):
    async def search(self, **kwargs: Any) -> FakeAsyncResults:
        self.search_calls.append(kwargs)
        await asyncio.Event().wait()
        raise AssertionError("unreachable")


def make_settings(**updates: object) -> Settings:
    values: dict[str, object] = {
        "azure_search_endpoint": "https://example.search.windows.net",
        "azure_search_index_name": "archive",
        "azure_image_search_index_name": "inq-betadam-images",
        "azure_search_semantic_configuration": "semantic",
        "azure_search_api_key": "secret",
    }
    values.update(updates)
    return Settings(**values)


def test_image_provider_uses_distinct_configured_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = FakeSearchClient()
    captured: dict[str, Any] = {}

    def build_client(**kwargs: Any) -> FakeSearchClient:
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(azure_image, "SearchClient", build_client)

    provider = AzureImageSearchProvider.from_settings(make_settings())

    assert provider.search_client is fake_client
    assert captured["endpoint"] == "https://example.search.windows.net"
    assert captured["index_name"] == "inq-betadam-images"


async def test_image_provider_builds_keyword_and_vector_search() -> None:
    fake_client = FakeSearchClient([[]])
    provider = AzureImageSearchProvider(make_settings(), fake_client)

    await provider.search(
        ImageSearchRequest(
            query="city hall",
            start_date="2024-01-01",
            end_date="2024-01-31",
            authors=["Jane Doe", "John Doe"],
            limit=5,
        )
    )

    kwargs = fake_client.search_calls[0]
    assert kwargs["search_text"] == "city hall"
    assert kwargs["search_fields"] == ["authors", "caption", "description"]
    assert kwargs["filter"] == (
        "(captured_date ge 2024-01-01T00:00:00Z "
        "and captured_date lt 2024-02-01T00:00:00Z) "
        "and (search.ismatch('Jane Doe', 'authors') "
        "or search.ismatch('John Doe', 'authors'))"
    )
    assert kwargs["top"] == 5
    assert kwargs["select"] == [
        "id",
        "image_url",
        "thumbnail_url",
        "screen_url",
        "authors",
        "caption",
        "description",
        "created_date",
        "captured_date",
    ]
    assert len(kwargs["vector_queries"]) == 1
    vector_query = kwargs["vector_queries"][0]
    assert vector_query.text == "city hall"
    assert vector_query.k_nearest_neighbors == 5
    assert vector_query.fields == "description_vector"
    assert "query_type" not in kwargs
    assert "semantic_configuration_name" not in kwargs


async def test_image_provider_search_everything_omits_vector_and_semantic_search() -> (
    None
):
    fake_client = FakeSearchClient([[]])
    provider = AzureImageSearchProvider(make_settings(), fake_client)

    await provider.search(ImageSearchRequest(query="*", authors=["Jane Doe"]))

    kwargs = fake_client.search_calls[0]
    assert kwargs["search_text"] == "*"
    assert kwargs["filter"] == "(search.ismatch('Jane Doe', 'authors'))"
    assert "vector_queries" not in kwargs
    assert "query_type" not in kwargs
    assert "semantic_configuration_name" not in kwargs


async def test_image_provider_maps_exact_result_contract() -> None:
    created = datetime(2024, 1, 2, 3, 4, tzinfo=UTC)
    captured = datetime(2024, 1, 3, 4, 5, tzinfo=UTC)
    fake_client = FakeSearchClient(
        [
            [
                {
                    "id": "image-1",
                    "image_url": "https://example.test/image.jpg",
                    "thumbnail_url": "https://example.test/thumb.jpg",
                    "screen_url": "https://example.test/screen.jpg",
                    "authors": "Jane Doe",
                    "caption": "A city hall press conference",
                    "description": "Officials speak at a lectern.",
                    "created_date": created,
                    "captured_date": captured,
                }
            ]
        ]
    )
    provider = AzureImageSearchProvider(make_settings(), fake_client)

    response = await provider.search(ImageSearchRequest(query="city hall"))

    assert response.count == 1
    assert response.results[0].model_dump() == {
        "id": "image-1",
        "image_url": "https://example.test/image.jpg",
        "thumbnail_url": "https://example.test/thumb.jpg",
        "screen_url": "https://example.test/screen.jpg",
        "authors": "Jane Doe",
        "caption": "A city hall press conference",
        "description": "Officials speak at a lectern.",
        "created_date": created,
        "captured_date": captured,
    }


async def test_image_provider_supports_explicit_field_mapping() -> None:
    mapping = AzureImageIndexFieldMapping(
        id="image_id",
        image_url="original",
        thumbnail_url="thumbnail",
        screen_url="screen",
        authors="byline",
        caption="title",
        description="alt_text",
        description_vector="alt_text_vector",
        created_date="created_at",
        captured_date="captured_at",
    )
    fake_client = FakeSearchClient(
        [[{"image_id": "image-1", "alt_text": "Officials speaking."}]]
    )
    provider = AzureImageSearchProvider(
        make_settings(),
        fake_client,
        field_mapping=mapping,
    )

    response = await provider.search(ImageSearchRequest(query="officials"))

    kwargs = fake_client.search_calls[0]
    assert kwargs["search_fields"] == ["byline", "title", "alt_text"]
    assert kwargs["vector_queries"][0].fields == "alt_text_vector"
    assert kwargs["select"] == [
        "image_id",
        "original",
        "thumbnail",
        "screen",
        "byline",
        "title",
        "alt_text",
        "created_at",
        "captured_at",
    ]
    assert response.results[0].id == "image-1"
    assert response.results[0].description == "Officials speaking."


async def test_image_provider_retries_transient_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def skip_backoff(_: float) -> None:
        return None

    monkeypatch.setattr("backoff._async.asyncio.sleep", skip_backoff)
    fake_client = FakeSearchClient([AzureError("first"), AzureError("second"), []])
    provider = AzureImageSearchProvider(make_settings(), fake_client)

    response = await provider.search(ImageSearchRequest(query="photo"))

    assert response.count == 0
    assert len(fake_client.search_calls) == 3


async def test_image_provider_maps_exhausted_errors_to_structured_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def skip_backoff(_: float) -> None:
        return None

    monkeypatch.setattr("backoff._async.asyncio.sleep", skip_backoff)
    fake_client = FakeSearchClient(
        [AzureError("first"), AzureError("second"), AzureError("third")]
    )
    provider = AzureImageSearchProvider(make_settings(), fake_client)

    with pytest.raises(SearchProviderError):
        await provider.search(ImageSearchRequest(query="photo"))

    assert len(fake_client.search_calls) == 3


async def test_image_provider_maps_timeout_to_structured_error() -> None:
    fake_client = HangingSearchClient()
    provider = AzureImageSearchProvider(
        make_settings(search_provider_timeout_seconds=0.001),
        fake_client,
    )

    with pytest.raises(SearchProviderTimeoutError):
        await provider.search(ImageSearchRequest(query="photo"))
