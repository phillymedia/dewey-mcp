# ADR 0015: Separate Runtime and Development Dependencies

**Status:** Accepted

## Context

Production needs only the packages required to serve MCP and call the active provider. Test, lint, formatting, notebook, and pre-commit tools increase installation size and attack surface without serving runtime traffic.

## Decision

Declare serving, validation, logging, and provider SDK packages as runtime dependencies. Keep tests, linting, formatting, notebooks, debugging, and pre-commit tooling in the uv development dependency group.

The production image installs from the lockfile without the development group.

## Consequences

- Production installs remain smaller and focused.
- Contributors use `uv sync --dev` to obtain the full maintenance environment.
- Dependency additions require choosing the correct group and updating `uv.lock`.
- A tool needed during image startup cannot live only in the development group.

## Related documentation

- [Development setup](../contributing.md#development-setup)
- [Docker preflight](../operations.md#docker-preflight)
