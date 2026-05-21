"""Provider-neutral request and response models."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_SEARCH_LIMIT = 20
DEFAULT_SEARCH_LIMIT = 10


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime(value.year, value.month, value.day, tzinfo=UTC)
    elif isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            raise ValueError("datetime value must not be blank")
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            parsed_date = date.fromisoformat(value)
            parsed = datetime(
                parsed_date.year,
                parsed_date.month,
                parsed_date.day,
                tzinfo=UTC,
            )
    else:
        raise ValueError("datetime value must be an ISO date or datetime")

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


class PublishedDateFilter(BaseModel):
    """Half-open Published Date range filter."""

    model_config = ConfigDict(extra="forbid")

    field: Literal["published_date"]
    start: datetime
    end: datetime

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_datetime(cls, value: object) -> datetime:
        return _parse_datetime(value)

    @model_validator(mode="after")
    def validate_range(self) -> PublishedDateFilter:
        if self.start >= self.end:
            raise ValueError("published_date filter start must be before end")
        return self


class AuthorFilter(BaseModel):
    """Author text-match filter."""

    model_config = ConfigDict(extra="forbid")

    field: Literal["author"]
    value: str = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("author filter value must not be blank")
        return normalized


SearchFilter = Annotated[
    PublishedDateFilter | AuthorFilter,
    Field(discriminator="field"),
]


class SearchRequest(BaseModel):
    """Structured MCP search request."""

    model_config = ConfigDict(extra="forbid")

    search_text: str
    filters: list[SearchFilter] = Field(default_factory=list)
    limit: int = Field(default=DEFAULT_SEARCH_LIMIT, ge=1, le=MAX_SEARCH_LIMIT)

    @field_validator("search_text")
    @classmethod
    def normalize_search_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("search_text is required and must not be blank")
        return normalized


class SearchResult(BaseModel):
    """One matching Article Chunk."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    article_id: str
    title: str | None = None
    published_date: datetime | None = None
    author: str | None = None
    link: str | None = None
    chunk_text: str
    score: float


class SearchResponse(BaseModel):
    """Structured MCP search response."""

    model_config = ConfigDict(extra="forbid")

    results: list[SearchResult]
    count: int

    @classmethod
    def from_results(cls, results: list[SearchResult]) -> SearchResponse:
        return cls(results=results, count=len(results))
