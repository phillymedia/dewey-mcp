"""Translate typed Search Filters into provider filter expressions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from dewey_mcp.models import AuthorFilter, PublishedDateFilter, SearchFilter


@dataclass(frozen=True)
class AzureFilterFieldNames:
    """Azure field names used for filter translation."""

    publish_date: str
    authors: str


def build_azure_filter(
    filters: list[SearchFilter],
    field_names: AzureFilterFieldNames,
) -> str | None:
    """Build an Azure AI Search OData filter from typed filters."""

    clauses = [_build_filter_clause(item, field_names) for item in filters]
    if not clauses:
        return None
    return " and ".join(f"({clause})" for clause in clauses)


def _build_filter_clause(
    search_filter: SearchFilter,
    field_names: AzureFilterFieldNames,
) -> str:
    if isinstance(search_filter, PublishedDateFilter):
        start = _format_azure_datetimeoffset(search_filter.start)
        end = _format_azure_datetimeoffset(search_filter.end)
        return (
            f"{field_names.publish_date} ge {start} "
            f"and {field_names.publish_date} lt {end}"
        )
    if isinstance(search_filter, AuthorFilter):
        return (
            f"search.ismatch('{_escape_odata_string(search_filter.value)}', "
            f"'{_escape_odata_string(field_names.authors)}')"
        )
    raise TypeError(f"Unsupported search filter: {search_filter!r}")


def _format_azure_datetimeoffset(value: datetime) -> str:
    normalized = value
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=UTC)
    normalized = normalized.astimezone(UTC)
    return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")


def _escape_odata_string(value: str) -> str:
    return value.replace("'", "''")
