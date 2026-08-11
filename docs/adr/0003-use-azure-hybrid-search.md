# ADR 0003: Use Azure Hybrid Search for the News Archive

**Status:** Accepted

## Context

News Archive search must serve agent workflows where relevance matters more than a minimal lexical-only implementation. The existing Azure index provides text, vector, and semantic search capabilities.

## Decision

Ordinary News Archive requests combine Azure keyword search, vector retrieval through the configured index vectorizer, and semantic ranking through the configured semantic profile. The adapter uses `text_vector` for vector retrieval.

Hybrid search is fixed internal behavior, not a caller-selectable MCP option. Search Everything (`*`) skips vector and semantic search and applies only filters and the result limit.

The Azure adapter owns the field mapping from `sourcepage`, `chunk`, `headline`, `publish_date`, `authors`, and `link` into Dewey's result contract.

## Consequences

- Callers receive the project's chosen relevance behavior through a simple provider-neutral contract.
- Runtime configuration must include the News Archive semantic configuration.
- Index vectorizer, semantic profile, or field changes require adapter and integration verification.
- Image search uses a related but distinct strategy because its index has no semantic configuration.

## Related documentation

- [Azure adapters](../architecture.md#azure-adapters)
- [ADR 0007](0007-isolate-search-provider-adapters.md)
- [ADR 0017](0017-image-hybrid-search-and-dual-readiness.md)
