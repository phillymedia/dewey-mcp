# ADR 0005: Use Streamable HTTP Transport

**Status:** Accepted

## Context

Dewey is a remotely hosted service for agents rather than a child process launched separately by every MCP client.

## Decision

Streamable HTTP is Dewey's only production MCP transport. The server binds to a configurable host, port, and path and runs as a containerized network service. Stdio transport is not supported.

## Consequences

- Clients need network access and must be configured with an HTTP endpoint.
- Deployment infrastructure owns routing, TLS, and client access control.
- Local troubleshooting must distinguish the MCP path from the health routes.
- The application does not need parallel stdio startup and lifecycle behavior.

## Related documentation

- [Connect an MCP client](../getting-started.md#connect-an-mcp-client)
- [Access control](../operations.md#access-control)
- [ADR 0011](0011-rely-on-infrastructure-access-control.md)
