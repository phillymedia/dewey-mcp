# Use Image Hybrid Search and Dual-Provider Readiness

Dewey MCP searches the Image Archive through a provider that is separate from the News Archive provider. The Azure implementation uses its own `SearchClient` for the `inq-betadam-images` index while sharing the configured Azure endpoint, authentication method, timeout budget, retry policy, and content-safe operational logging policy.

Ordinary Image Search Requests use hybrid retrieval: keyword search is restricted to `authors`, `caption`, and `description`, and vector retrieval uses `description_vector`. The image index has no semantic configuration, so image search does not request semantic ranking. Search Everything (`*`) omits vector retrieval and applies only the requested Captured Date and Author filters.

Image Search Results return image metadata and links only. Dewey MCP does not download, validate, proxy, or embed image bytes. This keeps the service a Read-only Gateway and avoids making remote image availability part of the search contract.

Readiness now represents the complete public search surface. `/readyz` reports ready only after both the News Archive provider and Image Archive provider respond to lightweight probes. A failure from either index returns the existing structured provider error and HTTP 503 without changing the health response format. Server shutdown closes both providers, including their independent Azure clients and credentials.
