# ADR 0016: Use a Non-root Production Container

**Status:** Accepted

## Context

Production container platforms commonly restrict root processes and writable application directories. Dewey does not need elevated privileges to serve HTTP or call Azure Search.

## Decision

Run the production image as a dedicated non-root user. Install only locked runtime dependencies, expose the configured MCP HTTP port, and avoid any requirement for a writable application directory.

## Consequences

- The image is compatible with more restrictive container policies.
- Runtime code cannot assume root privileges or write access to application files.
- Future dependencies and operational features must work under the non-root user.
- Local Docker preflight should exercise the same user as production.

## Related documentation

- [Docker preflight](../operations.md#docker-preflight)
- [ADR 0015](0015-separate-runtime-and-dev-dependencies.md)
