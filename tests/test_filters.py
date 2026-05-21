from dewey_mcp.filters import AzureFilterFieldNames, build_azure_filter
from dewey_mcp.models import SearchRequest


def test_build_azure_filter_combines_filters_with_and() -> None:
    request = SearchRequest(
        search_text="election",
        filters=[
            {
                "field": "published_date",
                "start": "1979-11-01",
                "end": "1979-12-01",
            },
            {"field": "author", "value": "George Will"},
        ],
    )

    expression = build_azure_filter(
        request.filters,
        AzureFilterFieldNames(publish_date="publish_date", authors="authors"),
    )

    assert expression == (
        "(publish_date ge 1979-11-01T00:00:00Z "
        "and publish_date lt 1979-12-01T00:00:00Z) "
        "and (search.ismatch('George Will', 'authors'))"
    )


def test_build_azure_filter_escapes_author_quotes() -> None:
    request = SearchRequest(
        search_text="column",
        filters=[{"field": "author", "value": "O'Connor"}],
    )

    expression = build_azure_filter(
        request.filters,
        AzureFilterFieldNames(publish_date="publish_date", authors="authors"),
    )

    assert expression == "(search.ismatch('O''Connor', 'authors'))"


def test_build_azure_filter_returns_none_for_no_filters() -> None:
    request = SearchRequest(search_text="election")

    assert (
        build_azure_filter(
            request.filters,
            AzureFilterFieldNames(publish_date="publish_date", authors="authors"),
        )
        is None
    )
