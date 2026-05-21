from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from dewey_mcp.models import SearchRequest


def test_search_request_defaults_limit_to_10() -> None:
    request = SearchRequest(search_text="Iran hostage crisis")

    assert request.limit == 10


def test_search_request_allows_search_everything_operator() -> None:
    request = SearchRequest(search_text=" * ")

    assert request.search_text == "*"


def test_search_request_rejects_blank_search_text() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(search_text=" ")


def test_search_request_enforces_hard_limit() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(search_text="Watergate", limit=21)


def test_published_date_filter_accepts_date_only_half_open_range() -> None:
    request = SearchRequest(
        search_text="Watergate",
        filters=[
            {
                "field": "published_date",
                "start": "1979-11-01",
                "end": "1979-12-01",
            }
        ],
    )

    date_filter = request.filters[0]
    assert date_filter.start == datetime(1979, 11, 1, tzinfo=UTC)
    assert date_filter.end == datetime(1979, 12, 1, tzinfo=UTC)


def test_published_date_filter_rejects_non_positive_range() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(
            search_text="Watergate",
            filters=[
                {
                    "field": "published_date",
                    "start": "1979-12-01",
                    "end": "1979-11-01",
                }
            ],
        )


def test_author_filter_normalizes_value() -> None:
    request = SearchRequest(
        search_text="election",
        filters=[{"field": "author", "value": " George Will "}],
    )

    author_filter = request.filters[0]
    assert author_filter.value == "George Will"
