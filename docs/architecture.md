# Architecture

Dewey MCP is a Read-only Gateway between MCP clients and two Azure AI Search indexes. The MCP layer owns the public contract; provider adapters own Azure-specific requests and response mapping.

## System shape

```text
MCP client
    │ streamable HTTP
    ▼
FastMCP tools and health routes        src/dewey_mcp/server.py
    │ validated Dewey request models
    ▼
Provider-neutral protocols             src/dewey_mcp/ports.py
    │
    ├── News Archive Azure adapter      providers/azure.py
    │       └── News Archive index
    │
    └── Image Archive Azure adapter     providers/azure_image.py
            └── Image Archive index
```

A normal search follows this sequence:

1. FastMCP accepts flat snake_case tool arguments.
2. A Pydantic request model normalizes and validates the arguments.
3. The tool calls a provider-neutral asynchronous protocol.
4. The Azure adapter translates filters, builds the Azure query, and maps Azure fields into Dewey result models.
5. The tool returns the response as both text JSON and structured MCP content.
6. Known provider failures become stable structured tool errors; invalid requests remain boundary validation errors.

This direction keeps Azure SDK types and query mechanics out of the public MCP contract.

## Module map

| Module | Responsibility |
| --- | --- |
| `__main__.py` | Load settings, configure JSON logging, build the server, and run streamable HTTP. |
| `server.py` | Register tools and health routes, record request-level telemetry, and manage provider lifecycles. |
| `models.py` | Define provider-neutral requests, results, responses, and validation. |
| `ports.py` | Define the asynchronous search, readiness, and close protocols. |
| `filters.py` | Translate validated date and Author filters into Azure OData expressions. |
| `errors.py` | Define internal error types and their public tool-error codes. |
| `settings.py` | Validate environment-backed runtime configuration. |
| `logging.py` | Format operational logs as JSON. |
| `providers/factory.py` | Select and construct configured providers. |
| `providers/azure.py` | Implement News Archive hybrid search and result mapping. |
| `providers/azure_image.py` | Implement Image Archive hybrid search and result mapping. |

## Public boundary

The server exposes only `search_archive` and `search_image_archive`, plus liveness and readiness HTTP routes. It deliberately does not expose Azure filter expressions, ranking modes, vector settings, index field names, or credentials.

Both request types share normalization and validation:

- Search Text is trimmed and cannot be blank.
- `*` explicitly means Search Everything.
- End dates cannot precede start dates.
- Blank Author values are removed and duplicate values are collapsed case-insensitively.
- Limits remain between 1 and 20.

See the [tool reference](tool-reference.md) for the public contract and [ADR 0001](adr/0001-typed-search-filters.md) for the boundary decision.

## Azure adapters

The two providers have independent `SearchClient` instances and index names. They share the Azure endpoint, credentials, timeout, retry policy, and safe-logging policy.

### News Archive

Ordinary searches combine keyword search, vector retrieval through the index vectorizer, and semantic ranking. The adapter uses this fixed field mapping:

| Azure field | Dewey use |
| --- | --- |
| `sourcepage` | Filename stem becomes `source_id` with a `doc_` prefix. |
| `chunk` | Article Chunk `text`. |
| `headline` | `title`. |
| `text_vector` | Vector retrieval. |
| `link` | `url`. |
| `authors` | Result `author` and Author filtering. |
| `publish_date` | `published_date` and date filtering. |

### Image Archive

Ordinary searches combine keyword search over `authors`, `caption`, and `description` with vector retrieval over `description_vector`. The image index does not use semantic ranking.

The adapter returns `id`, `image_url`, `thumbnail_url`, `screen_url`, `authors`, `caption`, `description`, `created_date`, and `captured_date`. Captured Date drives date filtering.

For both providers, Search Everything omits vector retrieval. Date filters are translated to half-open Azure ranges so an inclusive end date covers the full day. Author values are escaped before being passed to Azure `search.ismatch` expressions.

## Timeouts, retries, and errors

The configured provider timeout covers the complete search operation, including retries. Both Azure adapters retry HTTP 408, 429, 500, 502, 503, and 504 responses, plus non-HTTP Azure SDK failures, with exponential backoff for at most three total attempts. Exhausted Azure failures become `search_provider_unavailable`; an expired operation budget becomes `search_provider_timeout`.

An empty result set is always a successful response. Failures are never represented as empty results or fabricated Search Results.

## Process lifecycle

`/livez` only confirms that the web process can answer. `/readyz` probes the document count on both indexes and returns 503 if either provider is unavailable. This makes readiness represent the complete public search surface.

When FastMCP shuts down, Dewey closes both search clients and any `DefaultAzureCredential` instances. A failure closing one provider does not prevent an attempt to close the other.

## Logging and content safety

Container logs are JSON. Search events include operational metadata such as request duration, Search Text length, selected filter fields, requested limit, result count, and provider error category.

Logs do not include raw Search Text, Article Chunk text, Archived Image descriptions, credentials, or Azure error details. This keeps archive content in tool responses rather than service logs.

## Design constraints

- The service is read-only; ingestion and archive administration are out of scope.
- Streamable HTTP is the only transport.
- Infrastructure, not the application, controls client access.
- Index field mappings are code-defined, not environment-defined.
- A full provider plugin system remains out of scope while Azure is the only implementation.

The [ADR index](adr/README.md) links each constraint to its recorded decision.
