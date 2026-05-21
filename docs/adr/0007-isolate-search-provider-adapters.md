# Isolate Search Provider Adapters

Dewey MCP keeps provider-specific search code behind adapter modules. The MCP tool and core models depend on Dewey-owned request and result types; the Azure adapter is the only place that should know about Azure AI Search `SearchClient`, Azure query construction, semantic settings, vector profiles, and Azure response shapes.

This boundary keeps the initial Azure implementation testable and leaves room for future AWS search adapters without changing the MCP tool contract.

The codebase should define a small provider-neutral search interface now and implement only the Azure adapter in the first version. A full plugin system is intentionally out of scope until there is more than one real provider implementation.

The provider-neutral search interface is asynchronous so the MCP server can handle concurrent search calls while waiting on provider I/O.

Provider calls have an explicit configurable timeout, defaulting to 10 seconds for the whole search operation, so slow provider responses become bounded structured tool errors instead of unbounded MCP calls.

The Azure adapter uses the `backoff` library for transient provider failures, with at most two retries. If the provider still fails after retries are exhausted, the adapter returns a structured provider error to the MCP layer.
