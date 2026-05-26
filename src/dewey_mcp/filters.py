"""Translate flat SearchRequest fields into provider filter expressions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from dewey_mcp.models import SearchRequest


@dataclass(frozen=True)
class AzureFilterFieldNames:
    """Azure field names used for filter translation."""

    publish_date: str
    authors: str


def build_azure_filter(
    request: SearchRequest,
    field_names: AzureFilterFieldNames,
) -> str | None:
    """Build an Azure AI Search OData filter from a SearchRequest."""

    clauses = [
        clause
        for clause in (
            _published_date_clause(
                request.start_date, request.end_date, field_names.publish_date
            ),
            _authors_clause(request.authors, field_names.authors),
        )
        if clause is not None
    ]
    if not clauses:
        return None
    return " and ".join(f"({clause})" for clause in clauses)


def _published_date_clause(
    start: date | None,
    end: date | None,
    field: str,
) -> str | None:
    if start is None and end is None:
        return None

    parts: list[str] = []
    if start is not None:
        parts.append(f"{field} ge {_format_date_as_utc_midnight(start)}")
    if end is not None:
        # end_date is inclusive end-of-day; emit half-open lt next-day midnight.
        next_midnight = _format_date_as_utc_midnight(end + timedelta(days=1))
        parts.append(f"{field} lt {next_midnight}")
    return " and ".join(parts)


def _authors_clause(authors: list[str] | None, field: str) -> str | None:
    if not authors:
        return None

    escaped_field = _escape_odata_string(field)
    matches = [
        f"search.ismatch('{_escape_odata_string(author)}', '{escaped_field}')"
        for author in authors
    ]
    if len(matches) == 1:
        return matches[0]
    return " or ".join(matches)


def _format_date_as_utc_midnight(value: date) -> str:
    return f"{value.isoformat()}T00:00:00Z"


def _escape_odata_string(value: str) -> str:
    return value.replace("'", "''")
