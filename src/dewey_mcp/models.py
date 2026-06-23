"""Provider-neutral request and response models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_SEARCH_LIMIT = 20
DEFAULT_SEARCH_LIMIT = 10


AuthorList = Annotated[
    list[str],
    Field(
        min_length=1,
        description=(
            "Optional list of authors. Results must match one of " "these authors."
        ),
    ),
]


class SearchRequest(BaseModel):
    """Structured MCP search request."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "query": "university of the arts closure",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31",
                    "authors": ["John Smith", "Jane Doe"],
                }
            ]
        },
    )

    query: str = Field(
        min_length=1,
        description="Natural-language search query. Use '*' to search everything.",
    )

    start_date: date | None = Field(
        default=None,
        description="Inclusive lower bound for publish_date, in YYYY-MM-DD format.",
    )

    end_date: date | None = Field(
        default=None,
        description="Inclusive upper bound for publish_date, in YYYY-MM-DD format.",
    )

    authors: AuthorList | None = None

    limit: int = Field(default=DEFAULT_SEARCH_LIMIT, ge=1, le=MAX_SEARCH_LIMIT)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "query is required and must not be blank. Use '*' to search everything."
            )
        return normalized

    @field_validator("authors")
    @classmethod
    def normalize_authors(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None

        cleaned: list[str] = []
        seen: set[str] = set()

        for author in value:
            normalized = author.strip()
            if not normalized:
                continue

            key = normalized.casefold()
            if key not in seen:
                cleaned.append(normalized)
                seen.add(key)

        return cleaned or None

    @model_validator(mode="after")
    def validate_date_range(self) -> "SearchRequest":  # noqa: UP037
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be less than or equal to end_date.")
        return self


class SearchResult(BaseModel):
    """One matching Article Chunk."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    text: str
    title: str | None = None
    published_date: datetime | None = None
    author: str | None = None
    url: str | None = None


class SearchResponse(BaseModel):
    """Structured MCP search response."""

    model_config = ConfigDict(extra="forbid")

    results: list[SearchResult]
    count: int

    @classmethod
    def from_results(cls, results: list[SearchResult]) -> SearchResponse:
        return cls(results=results, count=len(results))
