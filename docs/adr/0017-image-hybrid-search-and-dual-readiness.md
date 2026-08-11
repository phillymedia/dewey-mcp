# ADR 0017: Use Image Hybrid Search and Dual-Provider Readiness

**Status:** Accepted

## Context

Dewey expanded from News Archive search to a separate Image Archive index. The image schema and relevance features differ: it provides descriptive metadata and a description vector but no semantic ranking configuration.

The public service should not report ready when one of its two advertised tools cannot reach its provider.

## Decision

Use a separate Image Archive provider and Azure `SearchClient`, while sharing the configured endpoint, authentication method, timeout, retry policy, and content-safe logging policy with News Archive search.

Ordinary image requests combine keyword search over `authors`, `caption`, and `description` with vector retrieval over `description_vector`. Search Everything (`*`) omits vector retrieval and applies Captured Date and Author filters only. Image search does not request semantic ranking.

Image Search Results contain metadata and links, not image bytes. Dewey does not download, validate, proxy, or embed the linked files.

Readiness succeeds only after both providers respond to lightweight probes. Shutdown closes both providers and their independent clients and credentials.

## Consequences

- Image relevance behavior fits the capabilities of its index without changing News Archive search.
- Image link availability is not part of the search or readiness contract.
- An outage of either index makes the complete service unready.
- Settings must include both index names, and lifecycle tests must cover both providers.

## Related documentation

- [Image tool reference](../tool-reference.md#search_image_archive)
- [Azure adapters](../architecture.md#azure-adapters)
- [Health checks](../operations.md#health-checks)
- [ADR 0010](0010-two-level-health-checks.md)
