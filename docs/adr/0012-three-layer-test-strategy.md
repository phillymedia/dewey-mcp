# ADR 0012: Use Three Test Layers

**Status:** Accepted

## Context

Core validation and translation logic needs fast feedback, MCP behavior needs verification at the server boundary, and Azure assumptions occasionally need checking against live services. Requiring Azure for every test would make routine development slow and credential-dependent.

## Decision

Maintain three test layers:

1. Unit tests for validation, filter translation, limits, result mapping, settings, retries, and isolated behavior.
2. MCP tool tests that assemble the server with fake providers.
3. Opt-in live Azure integration tests for real index and SDK assumptions.

The default test suite must require neither Azure credentials nor network access.

## Consequences

- Contributors get fast deterministic feedback locally and in CI.
- Tool behavior is tested independently from Azure behavior.
- Live tests remain necessary for assumptions fake clients cannot prove.
- New network calls need a fake or seam that keeps the default suite offline.

## Related documentation

- [Test strategy](../contributing.md#test-strategy)
- [ADR 0007](0007-isolate-search-provider-adapters.md)
