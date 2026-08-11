# ADR 0013: Use a `src` Package Layout

**Status:** Accepted

## Context

The initial root-level Python scaffold was not a maintainable home for server assembly, contracts, providers, configuration, logging, and errors. Tests also need to import the installed package rather than accidentally resolving a root working copy.

## Decision

Keep application code in the importable `src/dewey_mcp/` package. Separate server registration, models, provider protocols and adapters, filter translation, errors, settings, and logging into focused modules.

The `dewey-mcp` console script calls `dewey_mcp.__main__:main`.

## Consequences

- Imports and packaging exercise the same package layout used in production.
- Responsibilities have explicit module homes instead of accumulating in a root script.
- New application modules belong under `src/dewey_mcp/`.
- Packaging configuration must continue to include that package.

## Related documentation

- [Module map](../architecture.md#module-map)
- [Where changes belong](../contributing.md#where-changes-belong)
