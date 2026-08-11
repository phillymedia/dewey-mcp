# ADR 0001: Use Typed Search Filters

**Status:** Accepted

## Context

Agents need to narrow archive searches by dates and Authors. Passing raw Azure AI Search expressions through MCP would expose provider syntax, weaken validation, and couple the public contract to Azure.

## Decision

Dewey accepts Search Text plus allowlisted, typed Search Filters and translates them internally. The initial News Archive filters are Published Date and Author. Image Search later reuses the same request shape with Captured Date in place of Published Date.

Search Text is required and cannot be blank. The explicit `*` value means Search Everything. Date bounds are ranges, Author values use Azure text matching rather than exact identity, multiple filter kinds combine with `AND`, and multiple Authors combine with `OR`.

Pydantic validates the request at the MCP boundary. Agents never provide Azure OData expressions.

## Consequences

- The MCP contract stays provider-neutral and rejects unsupported fields and values early.
- Dewey owns date conversion, OData escaping, and Author-match semantics.
- Adding a filter requires coordinated model, translation, test, and documentation changes.
- Filter capabilities are intentionally narrower than Azure's full query language.

## Related documentation

- [Tool reference](../tool-reference.md#shared-request-fields)
- [Architecture](../architecture.md#public-boundary)
- [ADR 0017](0017-image-hybrid-search-and-dual-readiness.md)
