# Architecture Decision Records

Architecture Decision Records (ADRs) explain why Dewey's durable technical and product constraints exist. The current guides describe how the system behaves today; ADRs preserve the reasoning behind that behavior.

All listed decisions are accepted. If a future change reverses one, add a new ADR that marks the old decision as superseded rather than rewriting the history.

## MCP contracts

| ADR | Decision |
| --- | --- |
| [0001](0001-typed-search-filters.md) | Use validated, typed Search Filters instead of raw Azure expressions. |
| [0002](0002-search-results-return-snippets.md) | Return Article Chunks rather than complete News Articles. |
| [0008](0008-structured-tool-errors.md) | Represent failures as structured tool errors. |
| [0014](0014-use-snake-case-mcp-contracts.md) | Use snake_case public fields. |

## Search and provider architecture

| ADR | Decision |
| --- | --- |
| [0003](0003-use-azure-hybrid-search.md) | Use fixed Azure hybrid and semantic search for the News Archive. |
| [0007](0007-isolate-search-provider-adapters.md) | Keep provider mechanics behind asynchronous Dewey-owned interfaces. |
| [0017](0017-image-hybrid-search-and-dual-readiness.md) | Add separate Image Archive hybrid search and require both providers for readiness. |

## Runtime, operations, and security

| ADR | Decision |
| --- | --- |
| [0004](0004-env-var-configuration.md) | Configure Azure Search through validated environment variables. |
| [0005](0005-streamable-http-transport.md) | Use streamable HTTP as the production transport. |
| [0006](0006-use-fastmcp-uv-container.md) | Package the service with FastMCP, uv, and Docker. |
| [0009](0009-structured-operational-logging.md) | Emit content-safe structured logs. |
| [0010](0010-two-level-health-checks.md) | Separate liveness from dual-provider readiness. |
| [0011](0011-rely-on-infrastructure-access-control.md) | Enforce client access outside the application. |
| [0015](0015-separate-runtime-and-dev-dependencies.md) | Separate production and development dependencies. |
| [0016](0016-non-root-production-container.md) | Run the production image as a non-root user. |

## Engineering practices

| ADR | Decision |
| --- | --- |
| [0012](0012-three-layer-test-strategy.md) | Maintain unit, MCP tool, and opt-in live test layers. |
| [0013](0013-use-src-package-layout.md) | Keep application code in an importable `src` package. |

## ADR format

New ADRs use the next four-digit number and this structure:

```markdown
# ADR NNNN: Imperative decision title

**Status:** Proposed | Accepted | Superseded by ADR NNNN

## Context

What forces or problem require a decision?

## Decision

What did the team choose?

## Consequences

What becomes easier, harder, required, or intentionally unsupported?

## Related documentation

Links to current guides and related ADRs.
```

Keep current operational instructions in the main guides. An ADR should contain only enough implementation detail to make the decision and its consequences understandable later.
