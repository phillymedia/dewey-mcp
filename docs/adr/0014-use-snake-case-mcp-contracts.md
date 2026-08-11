# ADR 0014: Use snake_case MCP Contracts

**Status:** Accepted

## Context

The MCP contract is implemented with Python and Pydantic. Supporting a different external casing convention would require aliases and increase mapping and documentation overhead without a demonstrated client requirement.

## Decision

Public MCP request and response fields use snake_case, matching the Python model layer. Dewey does not add alternate casing aliases preemptively.

## Consequences

- Public JSON fields and internal model names remain easy to trace.
- Clients must send and read snake_case names exactly.
- A future casing compatibility layer should be added only for a real client need and must preserve backward compatibility.

## Related documentation

- [Tool reference](../tool-reference.md)
- [Public boundary](../architecture.md#public-boundary)
