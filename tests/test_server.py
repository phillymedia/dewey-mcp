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
        self.probe_calls = 0
        self.close_calls = 0

    async def search(self, request: SearchRequest) -> SearchResponse:
        self.requests.append(request)
        return SearchResponse.from_results(
            [
                SearchResult(
                    source_id="doc_article-1",
                    text="Chunk text",
                    title="Title",
                    published_date=None,
                    author="Author",
                    url="https://example.test/article-1",
                )
            ]
        )

    async def probe(self) -> None:
        self.probe_calls += 1

    async def close(self) -> None:
        self.close_calls += 1


class FailingProvider(FakeProvider):
    async def search(self, request: SearchRequest) -> SearchResponse:
        raise SearchProviderError()


class UnreadyProvider(FakeProvider):
    async def probe(self) -> None:
        self.probe_calls += 1
        raise SearchProviderError()


class FakeImageProvider:
    def __init__(self) -> None:
        self.requests: list[ImageSearchRequest] = []
        self.probe_calls = 0
        self.close_calls = 0

    async def search(self, request: ImageSearchRequest) -> ImageSearchResponse:
        self.requests.append(request)
        return ImageSearchResponse.from_results(
            [
                ImageSearchResult(
                    id="image-1",
                    image_url="https://example.test/image.jpg",
                    thumbnail_url=None,
                    screen_url="https://example.test/screen.jpg",
                    authors="Jane Photographer",
                    caption="City hall",
                    description="Officials speak at a lectern.",
                    created_date=None,
                    captured_date=None,
                )
            ]
        )

    async def probe(self) -> None:
        self.probe_calls += 1

    async def close(self) -> None:
        self.close_calls += 1


class FailingImageProvider(FakeImageProvider):
    async def search(self, request: ImageSearchRequest) -> ImageSearchResponse:
        raise SearchProviderError()


class UnreadyImageProvider(FakeImageProvider):
    async def probe(self) -> None:
        self.probe_calls += 1
        raise SearchProviderError()


def make_settings() -> Settings:
    return Settings(
        azure_search_endpoint="https://example.search.windows.net",
        azure_search_index_name="archive",
        azure_image_search_index_name="inq-betadam-images",
        azure_search_semantic_configuration="semantic",
        azure_search_api_key="secret",
    )


async def test_mcp_exposes_search_archive_tool_for_discovery() -> None:
    mcp = create_mcp(
        make_settings(),
        search_provider=FakeProvider(),
        image_search_provider=FakeImageProvider(),
    )

    tools = await mcp.list_tools()

    assert [tool.name for tool in tools] == [
        "search_archive",
        "search_image_archive",
    ]


async def test_search_archive_tool_calls_provider_with_validated_request() -> None:
    provider = FakeProvider()
    image_provider = FakeImageProvider()
    mcp = create_mcp(
        make_settings(),
        search_provider=provider,
        image_search_provider=image_provider,
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
    assert response.structuredContent["results"][0] == {
        "source_id": "doc_article-1",
        "text": "Chunk text",
        "title": "Title",
        "published_date": None,
        "author": "Author",
        "url": "https://example.test/article-1",
    }
    assert provider.requests[0].query == "hostage"
    assert provider.requests[0].authors == ["George Will"]
    assert provider.requests[0].limit == 5
    assert image_provider.requests == []


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


async def test_search_image_archive_calls_only_image_provider() -> None:
    archive_provider = FakeProvider()
    image_provider = FakeImageProvider()
    mcp = create_mcp(
        make_settings(),
        search_provider=archive_provider,
        image_search_provider=image_provider,
    )

    response = await mcp.call_tool(
        "search_image_archive",
        {
            "query": "  city hall  ",
            "start_date": "2024-01-01",
            "authors": [" Jane Photographer ", "jane photographer"],
            "limit": 5,
        },
    )

    assert not response.isError
    assert response.structuredContent == {
        "results": [
            {
                "id": "image-1",
                "image_url": "https://example.test/image.jpg",
                "thumbnail_url": None,
                "screen_url": "https://example.test/screen.jpg",
                "authors": "Jane Photographer",
                "caption": "City hall",
                "description": "Officials speak at a lectern.",
                "created_date": None,
                "captured_date": None,
            }
        ],
        "count": 1,
    }
    assert archive_provider.requests == []
    assert image_provider.requests[0].query == "city hall"
    assert image_provider.requests[0].authors == ["Jane Photographer"]
    assert image_provider.requests[0].limit == 5


async def test_search_image_archive_returns_structured_provider_error() -> None:
    mcp = create_mcp(
        make_settings(),
        search_provider=FakeProvider(),
        image_search_provider=FailingImageProvider(),
    )

    response = await mcp.call_tool(
        "search_image_archive",
        {"query": "city hall"},
    )

    assert response.isError
    assert response.structuredContent == {
        "error": "search_provider_unavailable",
        "message": "The archive search provider did not respond successfully.",
    }


def test_readiness_probes_both_providers() -> None:
    archive_provider = FakeProvider()
    image_provider = FakeImageProvider()
    mcp = create_mcp(
        make_settings(),
        search_provider=archive_provider,
        image_search_provider=image_provider,
    )

    with TestClient(mcp.streamable_http_app()) as client:
        response = client.get("/readyz")

        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
        assert archive_provider.probe_calls == 1
        assert image_provider.probe_calls == 1


async def test_lifespan_closes_both_providers() -> None:
    archive_provider = FakeProvider()
    image_provider = FakeImageProvider()
    mcp = create_mcp(
        make_settings(),
        search_provider=archive_provider,
        image_search_provider=image_provider,
    )

    async with mcp._mcp_server.lifespan(mcp._mcp_server):
        assert archive_provider.close_calls == 0
        assert image_provider.close_calls == 0

    assert archive_provider.close_calls == 1
    assert image_provider.close_calls == 1


def test_readiness_is_unready_when_image_provider_is_unavailable() -> None:
    archive_provider = FakeProvider()
    image_provider = UnreadyImageProvider()
    mcp = create_mcp(
        make_settings(),
        search_provider=archive_provider,
        image_search_provider=image_provider,
    )

    with TestClient(mcp.streamable_http_app()) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unready",
        "error": "search_provider_unavailable",
        "message": "The archive search provider did not respond successfully.",
    }
    assert archive_provider.probe_calls == 1
    assert image_provider.probe_calls == 1


def test_readiness_is_unready_when_archive_provider_is_unavailable() -> None:
    archive_provider = UnreadyProvider()
    image_provider = FakeImageProvider()
    mcp = create_mcp(
        make_settings(),
        search_provider=archive_provider,
        image_search_provider=image_provider,
    )

    with TestClient(mcp.streamable_http_app()) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unready",
        "error": "search_provider_unavailable",
        "message": "The archive search provider did not respond successfully.",
    }
    assert archive_provider.probe_calls == 1
    assert image_provider.probe_calls == 0
