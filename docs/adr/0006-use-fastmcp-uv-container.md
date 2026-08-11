# ADR 0006: Use FastMCP with uv and Docker

**Status:** Accepted

## Context

Dewey needs a small maintainable Python service with MCP support, reproducible dependency installation, and a production artifact suitable for a remote container platform.

## Decision

Build the service with FastMCP, manage and lock Python dependencies with uv, and package production as a Docker image. Use FastMCP's streamable HTTP support directly instead of adding a separate web framework.

The codebase may add middleware or service integrations later if a concrete requirement justifies them.

## Consequences

- Local and container environments resolve from `pyproject.toml` and `uv.lock`.
- FastMCP owns tool registration and HTTP serving.
- The production artifact and local preflight share the same Dockerfile.
- Contributors should avoid adding another web layer without a documented need.

## Related documentation

- [Development setup](../contributing.md#development-setup)
- [Docker preflight](../operations.md#docker-preflight)
- [ADR 0005](0005-streamable-http-transport.md)
