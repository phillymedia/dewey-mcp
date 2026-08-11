# ADR 0009: Use Structured Operational Logging

**Status:** Accepted

## Context

Operators need request, latency, result, and failure signals from a containerized service. Search Text and returned archive content may be sensitive and are not necessary for routine operational diagnosis.

## Decision

Dewey emits JSON logs with structured operational fields such as request identifier when available, Search Text length, selected filter fields, requested limit, result count, provider latency, and error category.

Logs exclude raw Search Text by default and must never include returned Article Chunk text. The same content-safe policy applies to image descriptions, credentials, and raw provider error details.

## Consequences

- Container platforms can index consistent machine-readable fields.
- Operators can monitor volume, latency, results, and failure classes without storing archive content.
- Debugging exact relevance issues requires controlled reproduction rather than reading raw queries from logs.
- New logging fields require a content-safety review.

## Related documentation

- [Structured logs](../operations.md#structured-logs)
- [Logging and content safety](../architecture.md#logging-and-content-safety)
