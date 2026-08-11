# Isolate Search Provider Adapters

Dewey MCP keeps provider-specific search code behind adapter modules. MCP tools and core models depend on Dewey-owned request and result types; Azure adapters are the only places that should know about Azure AI Search `SearchClient`, Azure query construction, semantic settings, vector profiles, and Azure response shapes.

This boundary keeps the initial Azure implementation testable and leaves room for future AWS search adapters without changing the MCP tool contract.

The codebase defines small provider-neutral search interfaces for the News Archive and Image Archive. A full plugin system is intentionally out of scope until there is more than one real backend implementation.

The provider-neutral search interface is asynchronous so the MCP server can handle concurrent search calls while waiting on provider I/O.

Provider calls have an explicit configurable timeout, defaulting to 10 seconds for the whole search operation, so slow provider responses become bounded structured tool errors instead of unbounded MCP calls.

The Azure adapter uses the `backoff` library for transient provider failures, with at most two retries. If the provider still fails after retries are exhausted, the adapter returns a structured provider error to the MCP layer.
