# ADR 0007: Isolate Search Provider Adapters

**Status:** Accepted

## Context

The initial implementation uses Azure AI Search, but the public MCP contract and core tests should not depend on Azure SDK objects, query syntax, or response shapes. Provider calls are asynchronous network operations that can be slow or fail transiently.

## Decision

MCP tools depend on Dewey-owned request and result models through small asynchronous protocols. Azure-specific clients, credentials, query construction, vector and semantic settings, field mappings, retries, and response mapping remain inside provider-facing modules.

Providers implement `search`, `probe`, and `close`. A provider operation has a configurable timeout, defaulting to 10 seconds. Azure calls retry transient failures with exponential backoff for at most three total attempts.

A full dynamic plugin system remains out of scope until real backend diversity demonstrates the need.

## Consequences

- MCP behavior can be tested with fake providers and no Azure credentials.
- A future backend can preserve the tool contract by implementing the same protocols.
- Backend exceptions must be translated into Dewey errors at the adapter boundary.
- Provider lifecycle and readiness are explicit parts of every implementation.

## Related documentation

- [Architecture](../architecture.md)
- [Adding a search provider](../contributing.md#adding-a-search-provider)
- [ADR 0008](0008-structured-tool-errors.md)
