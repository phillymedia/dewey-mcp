# ADR 0008: Return Structured Tool Errors

**Status:** Accepted

## Context

Callers must be able to distinguish a successful search with no matches from a provider failure. Returning error prose as a fabricated Search Result or an empty success would make that distinction unreliable.

## Decision

Validation failures are rejected at the MCP boundary. Known provider failures return MCP tool results with `isError: true`, a stable non-secret `error` code, and a safe `message`.

The current provider codes are `search_provider_unavailable` and `search_provider_timeout`. A successful search with no matches returns an empty `results` array and `count` of zero.

## Consequences

- Clients can branch on stable codes rather than parsing prose.
- Provider details and secrets remain out of public error responses.
- Adapters must translate expected backend failures into the Dewey error hierarchy.
- New public error categories require contract documentation and tests.

## Related documentation

- [Empty results and errors](../tool-reference.md#empty-results-and-errors)
- [Timeouts, retries, and errors](../architecture.md#timeouts-retries-and-errors)
