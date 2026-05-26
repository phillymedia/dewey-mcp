from dewey_mcp.filters import AzureFilterFieldNames, build_azure_filter
from dewey_mcp.models import SearchRequest

FIELD_NAMES = AzureFilterFieldNames(publish_date="publish_date", authors="authors")


def test_build_azure_filter_combines_filters_with_and() -> None:
    request = SearchRequest(
        query="election",
        start_date="1979-11-01",
        end_date="1979-11-30",
        authors=["George Will"],
    )

    expression = build_azure_filter(request, FIELD_NAMES)

    assert expression == (
        "(publish_date ge 1979-11-01T00:00:00Z "
        "and publish_date lt 1979-12-01T00:00:00Z) "
        "and (search.ismatch('George Will', 'authors'))"
    )


def test_build_azure_filter_combines_multiple_authors_with_or() -> None:
    request = SearchRequest(
        query="election",
        authors=["George Will", "Jane Doe"],
    )

    expression = build_azure_filter(request, FIELD_NAMES)

    assert expression == (
        "(search.ismatch('George Will', 'authors') "
        "or search.ismatch('Jane Doe', 'authors'))"
    )


def test_build_azure_filter_escapes_author_quotes() -> None:
    request = SearchRequest(query="column", authors=["O'Connor"])

    expression = build_azure_filter(request, FIELD_NAMES)

    assert expression == "(search.ismatch('O''Connor', 'authors'))"


def test_build_azure_filter_supports_open_ended_date_range() -> None:
    only_start = build_azure_filter(
        SearchRequest(query="x", start_date="2024-01-01"),
        FIELD_NAMES,
    )
    only_end = build_azure_filter(
        SearchRequest(query="x", end_date="2024-12-31"),
        FIELD_NAMES,
    )

    assert only_start == "(publish_date ge 2024-01-01T00:00:00Z)"
    assert only_end == "(publish_date lt 2025-01-01T00:00:00Z)"


def test_build_azure_filter_returns_none_for_no_filters() -> None:
    request = SearchRequest(query="election")

    assert build_azure_filter(request, FIELD_NAMES) is None
