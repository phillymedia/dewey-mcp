from datetime import date

import pytest
from pydantic import ValidationError

from dewey_mcp.models import ImageSearchRequest, ImageSearchResult, SearchRequest


def test_search_request_defaults_limit_to_10() -> None:
    request = SearchRequest(query="Iran hostage crisis")

    assert request.limit == 10


def test_search_request_defaults_authors_to_none() -> None:
    request = SearchRequest(query="Iran hostage crisis")

    assert request.authors is None


def test_search_request_allows_search_everything_operator() -> None:
    request = SearchRequest(query=" * ")

    assert request.query == "*"


def test_search_request_rejects_blank_query() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(query=" ")


def test_search_request_enforces_hard_limit() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(query="Watergate", limit=21)


def test_search_request_parses_date_strings() -> None:
    request = SearchRequest(
        query="Watergate",
        start_date="1979-11-01",
        end_date="1979-12-01",
    )

    assert request.start_date == date(1979, 11, 1)
    assert request.end_date == date(1979, 12, 1)


def test_search_request_rejects_inverted_date_range() -> None:
    with pytest.raises(ValidationError):
        SearchRequest(
            query="Watergate",
            start_date="1979-12-01",
            end_date="1979-11-01",
        )


def test_search_request_allows_open_ended_date_range() -> None:
    only_start = SearchRequest(query="x", start_date="2024-01-01")
    only_end = SearchRequest(query="x", end_date="2024-12-31")

    assert only_start.end_date is None
    assert only_end.start_date is None


def test_search_request_normalizes_authors() -> None:
    request = SearchRequest(
        query="election",
        authors=[" George Will ", "george will", "", "Jane Doe"],
    )

    assert request.authors == ["George Will", "Jane Doe"]


def test_search_request_returns_none_when_authors_collapse_to_empty() -> None:
    request = SearchRequest(query="election", authors=["  ", ""])

    assert request.authors is None


def test_image_search_request_reuses_search_validation_and_normalization() -> None:
    request = ImageSearchRequest(
        query="  newsroom  ",
        start_date="2024-01-01",
        end_date="2024-01-31",
        authors=[" Jane Doe ", "jane doe", ""],
    )

    assert request.query == "newsroom"
    assert request.start_date == date(2024, 1, 1)
    assert request.end_date == date(2024, 1, 31)
    assert request.authors == ["Jane Doe"]
    assert request.limit == 10


@pytest.mark.parametrize(
    "values",
    [
        {"query": " "},
        {"query": "photo", "limit": 21},
        {
            "query": "photo",
            "start_date": "2024-02-01",
            "end_date": "2024-01-01",
        },
    ],
)
def test_image_search_request_rejects_invalid_values(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ImageSearchRequest(**values)


def test_image_result_requires_id_but_allows_nullable_metadata() -> None:
    result = ImageSearchResult(id="image-1")

    assert result.model_dump() == {
        "id": "image-1",
        "image_url": None,
        "thumbnail_url": None,
        "screen_url": None,
        "authors": None,
        "caption": None,
        "description": None,
        "created_date": None,
        "captured_date": None,
    }

    with pytest.raises(ValidationError):
        ImageSearchResult()
