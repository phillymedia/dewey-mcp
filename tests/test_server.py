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


async def test_search_archive_tool_calls_provider_with_validated_request() -> None:
    provider = FakeProvider()
    mcp = create_mcp(make_settings(), search_provider=provider)

    response = await mcp.call_tool(
        "search_archive",
        {
            "search_text": "hostage",
            "filters": [{"field": "author", "value": " George Will "}],
            "limit": 5,
        },
    )

    assert not response.isError
    assert response.structuredContent is not None
    assert response.structuredContent["count"] == 1
    assert provider.requests[0].search_text == "hostage"
    assert provider.requests[0].filters[0].value == "George Will"
    assert provider.requests[0].limit == 5


async def test_search_archive_tool_returns_structured_provider_error() -> None:
    mcp = create_mcp(make_settings(), search_provider=FailingProvider())

    response = await mcp.call_tool(
        "search_archive",
        {"search_text": "hostage"},
    )

    assert response.isError
    assert response.structuredContent == {
        "error": "search_provider_unavailable",
        "message": "The archive search provider did not respond successfully.",
    }
