# ADR 0011: Rely on Infrastructure Access Control

**Status:** Accepted

## Context

Dewey runs as a remote HTTP service, but the initial application does not need to own user identities, sessions, or authorization policy. Those controls already exist at common deployment boundaries.

## Decision

The FastMCP application does not authenticate MCP clients. Production deployments must protect it with private networking, a gateway, platform authentication, or equivalent infrastructure controls.

Application-level authentication may be added later if a concrete deployment model requires it.

## Consequences

- The application remains smaller and has no credential or session protocol of its own.
- A direct public deployment is unsafe and outside the supported deployment model.
- Operators must verify access controls independently of Dewey health checks.
- A future application-auth design will require a new ADR and client migration plan.

## Related documentation

- [Access control](../operations.md#access-control)
- [ADR 0005](0005-streamable-http-transport.md)
