from starlette.testclient import TestClient

from dewey_mcp.errors import SearchProviderError
from dewey_mcp.models import (
    ImageSearchRequest,
    ImageSearchResponse,
    ImageSearchResult,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from dewey_mcp.server import create_mcp
from dewey_mcp.settings import Settings


class FakeProvider:
    def __init__(self) -> None:
        self.requests: list[SearchRequest] = []

    async def search(self, request: SearchRequest) -> SearchResponse:
        self.requests.append(request)
        return SearchResponse.from_results(
            [
                SearchResult(
                    chunk_id="chunk-1",
                    article_id="article-1",
                    title="Title",
                    published_date=None,
                    author="Author",
                    link="https://example.test/article-1",
                    chunk_text="Chunk text",
                    score=1.0,
                )
            ]
        )

    async def probe(self) -> None:
        return None

    async def close(self) -> None:
        return None


class FakeImageProvider:
    def __init__(self) -> None:
        self.requests: list[ImageSearchRequest] = []

    async def search(self, request: ImageSearchRequest) -> ImageSearchResponse:
        self.requests.append(request)
        return ImageSearchResponse.from_results(
            [
                ImageSearchResult(
                    image_id="image-1",
                    image_url="https://example.test/image-1.jpg",
                    caption="Ribbon cutting",
                    description="Officials cut a ribbon at city hall.",
                    authors="Photo Staff",
                    capture_date=None,
                    score=1.0,
                )
            ]
        )

    async def probe(self) -> None:
        return None

    async def close(self) -> None:
        return None


class FailingProvider(FakeProvider):
    async def search(self, request: SearchRequest) -> SearchResponse:
        raise SearchProviderError()


class FailingImageProvider(FakeImageProvider):
    async def search(self, request: ImageSearchRequest) -> ImageSearchResponse:
        raise SearchProviderError()

    async def probe(self) -> None:
        raise SearchProviderError()


def make_settings() -> Settings:
    return Settings(
        azure_search_endpoint="https://example.search.windows.net",
        azure_search_index_name="archive",
        azure_search_semantic_configuration="semantic",
        azure_image_search_index_name="images",
        azure_image_search_semantic_configuration="image-semantic",
        azure_search_api_key="secret",
    )


async def test_mcp_exposes_search_archive_tool_for_discovery() -> None:
    mcp = create_mcp(
        make_settings(),
        search_provider=FakeProvider(),
        image_search_provider=FakeImageProvider(),
    )

    tools = await mcp.list_tools()

    assert [tool.name for tool in tools] == ["search_archive", "search_images"]


async def test_search_archive_tool_calls_provider_with_validated_request() -> None:
    provider = FakeProvider()
    mcp = create_mcp(
        make_settings(),
        search_provider=provider,
        image_search_provider=FakeImageProvider(),
    )

    response = await mcp.call_tool(
        "search_archive",
        {
            "query": "hostage",
            "authors": [" George Will "],
            "limit": 5,
        },
    )

    assert not response.isError
    assert response.structuredContent is not None
    assert response.structuredContent["count"] == 1
    assert provider.requests[0].query == "hostage"
    assert provider.requests[0].authors == ["George Will"]
    assert provider.requests[0].limit == 5


async def test_search_images_tool_calls_provider_with_validated_request() -> None:
    provider = FakeImageProvider()
    mcp = create_mcp(
        make_settings(),
        search_provider=FakeProvider(),
        image_search_provider=provider,
    )

    response = await mcp.call_tool(
        "search_images",
        {
            "query": " ribbon cutting ",
            "authors": [" Photo Staff ", "photo staff"],
            "limit": 5,
        },
    )

    assert not response.isError
    assert response.structuredContent is not None
    assert response.structuredContent["count"] == 1
    assert provider.requests[0].query == "ribbon cutting"
    assert provider.requests[0].authors == ["Photo Staff"]
    assert provider.requests[0].limit == 5


async def test_search_archive_tool_returns_structured_provider_error() -> None:
    mcp = create_mcp(
        make_settings(),
        search_provider=FailingProvider(),
        image_search_provider=FakeImageProvider(),
    )

    response = await mcp.call_tool(
        "search_archive",
        {"query": "hostage"},
    )

    assert response.isError
    assert response.structuredContent == {
        "error": "search_provider_unavailable",
        "message": "The archive search provider did not respond successfully.",
    }


async def test_search_images_tool_returns_structured_provider_error() -> None:
    mcp = create_mcp(
        make_settings(),
        search_provider=FakeProvider(),
        image_search_provider=FailingImageProvider(),
    )

    response = await mcp.call_tool(
        "search_images",
        {"query": "ribbon"},
    )

    assert response.isError
    assert response.structuredContent == {
        "error": "search_provider_unavailable",
        "message": "The archive search provider did not respond successfully.",
    }


def test_readiness_returns_per_provider_status_when_ready() -> None:
    mcp = create_mcp(
        make_settings(),
        search_provider=FakeProvider(),
        image_search_provider=FakeImageProvider(),
    )

    with TestClient(mcp.streamable_http_app()) as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "providers": {
            "archive": {"status": "ready"},
            "images": {"status": "ready"},
        },
    }


def test_readiness_returns_503_with_partial_provider_status() -> None:
    mcp = create_mcp(
        make_settings(),
        search_provider=FakeProvider(),
        image_search_provider=FailingImageProvider(),
    )

    with TestClient(mcp.streamable_http_app()) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unready",
        "providers": {
            "archive": {"status": "ready"},
            "images": {
                "status": "unready",
                "error": "search_provider_unavailable",
                "message": "The archive search provider did not respond successfully.",
            },
        },
    }
