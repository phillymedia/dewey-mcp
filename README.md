# Dewey MCP

Dewey MCP is a containerized [FastMCP](https://github.com/modelcontextprotocol/python-sdk)
server that gives agents read-only search over news and image archives backed
by Azure AI Search. It is a **read-only gateway**: it returns search results
but never ingests, updates, deletes, or reindexes articles or images.

## Domain language

The codebase, docs, and ADRs use a consistent vocabulary:

| Term | Meaning |
| --- | --- |
| News Archive | The collection of historical and current news articles (1978 to present). |
| News Article | A single published story. |
| Article Chunk | A searchable excerpt of a News Article. One article can have many chunks. |
| Image Archive | The collection of historical and current searchable image metadata. |
| Archived Image | A single image described by metadata and remote links in the Image Archive. |
| Search Request | An agent's request: search text plus optional filters and a result limit. |
| Search Result | One matching Article Chunk plus the article metadata needed to judge relevance. |
| Image Search Result | One matching Archived Image plus metadata and image links. |
| Search Everything | The explicit `*` query value: return results constrained only by filters. |

## The `search_archive` tool

The server exposes `search_archive` with flat parameters:

| Parameter | Type | Notes |
| --- | --- | --- |
| `query` | `str` (required) | Natural-language search text. Use `*` to search everything (filters only). Must not be blank. |
| `start_date` | `YYYY-MM-DD` (optional) | Inclusive lower bound on the article's publish date. |
| `end_date` | `YYYY-MM-DD` (optional) | Inclusive upper bound (end of day). Must not be before `start_date`. |
| `authors` | `list[str]` (optional) | Results match **any one** of the listed authors (OR semantics). Author matching is text match, not exact identity. |
| `limit` | `int` (optional) | Default `10`, hard maximum `20`. |

Example call:

```json
{
  "query": "Iran hostage crisis",
  "start_date": "1979-11-01",
  "end_date": "1979-12-01",
  "authors": ["George Will"],
  "limit": 10
}
```

The response contains `results` (a list of Search Results) and `count`. Each
result is one Article Chunk:

```json
{
  "source_id": "doc_...",
  "text": "...",
  "title": "...",
  "published_date": "1979-11-15T00:00:00Z",
  "author": "...",
  "url": "..."
}
```

An empty `results` list is a successful search with no matches. Provider
failures come back as structured tool errors (`isError: true`) with stable,
non-secret codes: `search_provider_unavailable` and `search_provider_timeout`.

Behind the tool, the Azure adapter runs **hybrid search**: text search plus
vector search (via the index's vectorizer profile) with semantic ranking. A
`*` query skips the vector/semantic path and runs filters-only retrieval.
Hybrid search is fixed internal behavior, not agent-selectable (see
[ADR 0003](docs/adr/0003-use-azure-hybrid-search.md)).

## The `search_image_archive` tool

The `search_image_archive` tool searches Archived Images and accepts the same
flat request shape with image-specific date semantics:

| Parameter | Type | Notes |
| --- | --- | --- |
| `query` | `str` (required) | Natural-language search text. Use `*` to search everything (filters only). Must not be blank. |
| `start_date` | `YYYY-MM-DD` (optional) | Inclusive lower bound on `captured_date`. |
| `end_date` | `YYYY-MM-DD` (optional) | Inclusive upper bound (end of day) on `captured_date`. Must not be before `start_date`. |
| `authors` | `list[str]` (optional) | Results match **any one** of the listed authors (OR semantics). |
| `limit` | `int` (optional) | Default `10`, hard maximum `20`. |

Example call:

```json
{
  "query": "city hall press conference",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "authors": ["Jane Photographer"],
  "limit": 10
}
```

Every Image Search Result contains exactly these nine fields. All metadata may
be `null`; only `id` is required. The response wrapper is `{results, count}`,
the same as `search_archive`.

```json
{
  "id": "image-1",
  "image_url": "https://example.test/image.jpg",
  "thumbnail_url": "https://example.test/thumbnail.jpg",
  "screen_url": "https://example.test/screen.jpg",
  "authors": "Jane Photographer",
  "caption": "City hall press conference",
  "description": "Officials speak at a lectern.",
  "created_date": "2024-01-02T10:00:00Z",
  "captured_date": "2024-01-01T14:30:00Z"
}
```

The links are metadata only; Dewey does not download, validate, proxy, or
embed image bytes. Ordinary image queries combine keyword search over
`authors`, `caption`, and `description` with vector retrieval over
`description_vector`. The image index has no semantic ranking configuration.
As with article search, `*` skips vector retrieval and applies filters only.
Image searches use the same structured timeout and provider-error contract.
See [ADR 0017](docs/adr/0017-image-hybrid-search-and-dual-readiness.md).

## Architecture

The code lives in a `src/` package layout. The MCP layer depends only on
Dewey-owned models and a provider-neutral interface; all Azure-specific code is
isolated in the provider adapter.

```text
src/dewey_mcp/
├── __main__.py        # CLI entrypoint: load settings, configure logging, run server
├── server.py          # Both search tools plus /livez and /readyz
├── models.py          # Provider-neutral article and image search models
├── ports.py           # Article/image provider protocols (search/probe/close)
├── filters.py         # Translates SearchRequest fields into Azure OData filters
├── errors.py          # DeweyMcpError hierarchy → structured tool errors
├── settings.py        # Env-backed Settings (pydantic-settings)
├── logging.py         # Structured operational logging setup
└── providers/
    ├── azure.py       # News Archive hybrid search adapter
    ├── azure_image.py # Image Archive hybrid search adapter (no semantic ranking)
    └── factory.py     # Builds both providers from settings
```

Key behaviors to know:

- **Validation at the boundary.** Pydantic request models enforce non-blank
  queries, valid date ranges, deduplicated authors, and limits of 1–20. Agents
  never send raw Azure filter syntax; `filters.py` owns the translation
  (half-open date ranges, `search.ismatch` for authors, OData string escaping).
- **Provider isolation.** `ports.ArchiveSearchProvider` and
  `ports.ImageSearchProvider` are the interfaces the server knows. Both Azure
  adapters wrap calls in a configurable timeout (default 10 s) and retry
  transient failures (408/429/5xx) up to two times with exponential backoff
  before surfacing a structured error.
- **Two-level health checks.** `/livez` says the process is up; `/readyz`
  probes both Azure Search indexes (document count) and returns `503` when
  either provider is unreachable.
- **Logging never includes content.** Logs carry query length, filter fields,
  limit, result count, and latency — never returned result text or raw search
  text.

Design decisions are recorded as ADRs in [`docs/adr/`](docs/adr/). Read those
first when changing the tool contract, provider behavior, or deployment shape.

## Configuration

All configuration comes from environment variables (and a local `.env` file —
`.env.local` is *not* read automatically). Copy `.env.template` to get started.

Required:

```text
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_INDEX_NAME=
AZURE_IMAGE_SEARCH_INDEX_NAME=inq-betadam-images
AZURE_SEARCH_SEMANTIC_CONFIGURATION=
```

Optional (defaults shown):

```text
AZURE_SEARCH_API_KEY=            # if unset, DefaultAzureCredential is used
LOG_LEVEL=INFO
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_PATH=/mcp
HEALTH_LIVENESS_PATH=/livez
HEALTH_READINESS_PATH=/readyz
SEARCH_PROVIDER=azure            # only "azure" is supported today
SEARCH_PROVIDER_TIMEOUT_SECONDS=10
```

Missing required settings fail fast at startup with a validation error.

The Azure index field mappings are defined in code in `providers/azure.py` and
`providers/azure_image.py`, not in the environment. The News Archive mapping
expects these index fields:

```text
sourcepage   -> source_id (filename stem prefixed with "doc_")
chunk        -> text
headline     -> title
text_vector  -> (vector search)
link         -> url
authors      -> author
publish_date -> published_date
```

The Image Archive mapping expects these fields:

```text
id                 -> id
image_url          -> image_url
thumbnail_url      -> thumbnail_url
screen_url         -> screen_url
authors            -> authors (keyword search and Author filtering)
caption            -> caption (keyword search)
description        -> description (keyword search)
description_vector -> (vector search)
created_date       -> created_date
captured_date      -> captured_date (date filtering)
```

## Development

The project uses [uv](https://docs.astral.sh/uv/) and Python 3.11+.

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run black --check .
uv run pre-commit install
```

Tests follow a three-layer strategy (see
[ADR 0012](docs/adr/0012-three-layer-test-strategy.md)): unit tests for
validation, filter translation, and result mapping; MCP tool tests against a
fake provider; and opt-in live Azure integration tests. The default
`uv run pytest` run requires no Azure credentials or network access.

Run locally:

```bash
cp .env.template .env
# Fill in the required Azure settings in .env, then run:
uv run dewey-mcp
```

If you keep local secrets in `.env.local` instead of `.env`, source it before
starting the server:

```bash
set -a
source .env.local
set +a
uv run dewey-mcp
```

## MCP client configuration

Dewey exposes MCP over **streamable HTTP** at `MCP_PATH` (default `/mcp`).
With the default host and port, clients connect to:

```text
http://127.0.0.1:8000/mcp
```

There is no stdio transport. If a client shows no tools, confirm the server
started with the required Azure settings loaded and that the client is using
streamable HTTP against the `/mcp` endpoint.

## Docker preflight

Before pushing an image for Azure Container Apps, build and run the production
container locally:

```bash
docker build -t dewey-mcp:local .
docker run --rm --name dewey-mcp-local --env-file .env.local -p 8000:8000 dewey-mcp:local
```

Use `.env` instead of `.env.local` if that is where your local settings live.
`--env-file` passes values into the running container process; it does not bake
secrets into the image. The image runs as a non-root user and installs only
runtime dependencies.

In another terminal, verify that the container is listening and that Azure
Search is reachable:

```bash
curl http://127.0.0.1:8000/livez   # {"status":"ok"} when the process is running
curl http://127.0.0.1:8000/readyz  # {"status":"ready"} when config + Azure probe succeed
```

Follow logs and stop the container:

```bash
docker logs -f dewey-mcp-local
docker stop dewey-mcp-local
```

If port `8000` is taken locally, map a different host port
(`-p 8080:8000`) and curl `127.0.0.1:8080` instead.

For Azure Container App parity, confirm the image listens on container port
`8000` with endpoints `/mcp`, `/livez`, and `/readyz` (unless overridden by
environment variables), and that the Container App provides all four required
Azure Search settings. An API key is the simplest preflight auth path;
without one, the container falls back to default Azure credentials, which
usually need extra setup outside Azure.

Troubleshooting:

- Container exits immediately → check the required Azure Search settings;
  invalid configuration fails fast at startup.
- `/livez` ok but `/readyz` returns `503` → the process is running but an
  Azure Search probe is failing: check both index configurations,
  authentication, and network access to the search endpoint.

## Deployment

Deployment is automated. Every push to `main` triggers the GitHub Actions
workflow in
[`.github/workflows/`](.github/workflows/app-dewey-mcp-AutoDeployTrigger-ee413151-e45a-4f11-b61f-34e9eca54c9f.yml)
(generated by Azure Container Apps), which:

1. Logs in to Azure with OIDC (no long-lived credentials in the repo).
2. Builds the container image from the repo's `Dockerfile` and pushes it to
   Azure Container Registry (`deweymcpacaenvafa2db.azurecr.io`), tagged with
   the commit SHA.
3. Deploys the image to the `app-dewey-mcp` Container App in the
   `dewey-mcp-aca-env` resource group.

The workflow can also be run manually from the GitHub Actions tab
(`workflow_dispatch`).

Things to know:

- **Merging to `main` is deploying.** There is no separate release step, so
  run the Docker preflight (above) and the test suite before merging.
- **Runtime configuration lives on the Container App**, not in the image. The
  Container App must provide `AZURE_SEARCH_ENDPOINT`,
  `AZURE_SEARCH_INDEX_NAME`, `AZURE_IMAGE_SEARCH_INDEX_NAME`, and
  `AZURE_SEARCH_SEMANTIC_CONFIGURATION`; in Azure, prefer managed identity
  over `AZURE_SEARCH_API_KEY`.
- **Credentials are GitHub repo secrets** (`APPDEWEYMCP_AZURE_CLIENT_ID`,
  `APPDEWEYMCP_AZURE_TENANT_ID`, `APPDEWEYMCP_AZURE_SUBSCRIPTION_ID`, plus
  registry username/password). Rotate or update them in the repo settings,
  not in the workflow file.
- **Client access control is infrastructure's job.** The app does no MCP
  client authentication itself (see
  [ADR 0011](docs/adr/0011-rely-on-infrastructure-access-control.md)); deploy
  behind private networking, a gateway, or platform auth.
- After a deploy, verify health: `/livez` for the process, `/readyz` for
  config + reachability of both Azure Search indexes.

## Adding a new search provider

1. Implement the appropriate `ArchiveSearchProvider` or `ImageSearchProvider`
   protocol (`ports.py`): async `search`, `probe`, and `close`.
2. Keep all provider-specific query construction and response mapping inside
   your adapter module under `providers/`.
3. Register it in `providers/factory.py` and extend the `SEARCH_PROVIDER`
   literal in `settings.py`.
4. Surface failures as `SearchProviderError` / `SearchProviderTimeoutError` so
   the MCP layer returns stable structured errors.

See [ADR 0007](docs/adr/0007-isolate-search-provider-adapters.md) for the
boundary rules.
