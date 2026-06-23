from dewey_mcp.errors import SearchProviderError
from dewey_mcp.models import SearchRequest, SearchResponse, SearchResult
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
        return None

    async def close(self) -> None:
        return None


class FailingProvider(FakeProvider):
    async def search(self, request: SearchRequest) -> SearchResponse:
        raise SearchProviderError()


def make_settings() -> Settings:
    return Settings(
        azure_search_endpoint="https://example.search.windows.net",
        azure_search_index_name="archive",
        azure_search_semantic_configuration="semantic",
        azure_search_api_key="secret",
    )


async def test_mcp_exposes_search_archive_tool_for_discovery() -> None:
    mcp = create_mcp(make_settings(), search_provider=FakeProvider())

    tools = await mcp.list_tools()

    assert [tool.name for tool in tools] == ["search_archive"]


async def test_search_archive_tool_calls_provider_with_validated_request() -> None:
    provider = FakeProvider()
    mcp = create_mcp(make_settings(), search_provider=provider)

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


async def test_search_archive_tool_returns_structured_provider_error() -> None:
    mcp = create_mcp(make_settings(), search_provider=FailingProvider())

    response = await mcp.call_tool(
        "search_archive",
        {"query": "hostage"},
    )

    assert response.isError
    assert response.structuredContent == {
        "error": "search_provider_unavailable",
        "message": "The archive search provider did not respond successfully.",
    }
