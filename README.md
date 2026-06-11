# Dewey MCP

Dewey MCP is a containerized FastMCP server for read-only search over news and
image archives backed by Azure AI Search.

## Tools

`search_archive` searches the News Archive and returns matching article chunks.
It accepts:

```json
{
  "query": "Iran hostage crisis",
  "start_date": "1979-11-01",
  "end_date": "1979-12-01",
  "authors": ["George Will"],
  "limit": 10
}
```

`query` is required. Use `*` to search everything with filters only. Date filters
are inclusive calendar dates. Multiple filters are combined with `AND`, and
multiple authors match any author. `limit` defaults to `10` and has a hard
maximum of `20`.

Each `search_archive` result is one matching article chunk:

```json
{
  "chunk_id": "...",
  "article_id": "...",
  "title": "...",
  "published_date": "1979-11-15T00:00:00Z",
  "author": "...",
  "link": "...",
  "chunk_text": "...",
  "score": 1.23
}
```

`search_images` searches the Image Archive by image description and returns
matching image metadata. It accepts:

```json
{
  "query": "city hall ribbon cutting",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "authors": ["Photo Staff"],
  "limit": 10
}
```

Each `search_images` result is one matching image:

```json
{
  "image_id": "...",
  "image_url": "https://example.test/image.jpg",
  "caption": "...",
  "description": "...",
  "authors": "...",
  "capture_date": "2024-05-01T00:00:00Z",
  "score": 1.23
}
```

Dewey returns image URLs as metadata only. It does not fetch, validate, proxy, or
serve image bytes.

## Configuration

Required:

```text
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_INDEX_NAME=
AZURE_SEARCH_SEMANTIC_CONFIGURATION=
AZURE_IMAGE_SEARCH_INDEX_NAME=
AZURE_IMAGE_SEARCH_SEMANTIC_CONFIGURATION=
```

Optional:

```text
AZURE_SEARCH_API_KEY=
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_PATH=/mcp
SEARCH_PROVIDER_TIMEOUT_SECONDS=10
```

If `AZURE_SEARCH_API_KEY` is not set, the Azure adapter uses default Azure
credentials.

Dewey reads environment variables from the process environment and from a local
`.env` file. It does not automatically read `.env.local`.

The Azure index field mappings are defined in the Azure provider code, not in
the environment. The default News Archive mapping expects:

```text
chunk_id -> chunk_id
chunk -> chunk_text
headline -> title
text_vector -> vector search
link -> link
authors -> author
publish_date -> published_date
parent_id -> article_id
```

The default Image Archive mapping expects:

```text
image_id -> image_id
image_url -> image_url
caption -> caption
description -> description
authors -> authors
capture_date -> capture_date
description_vector -> vector search
```

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run black --check .
uv run pre-commit install
```

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

## Docker preflight

Before pushing an image for Azure Container Apps, build and run the production
container locally:

```bash
docker build -t dewey-mcp:local .
docker run --rm --name dewey-mcp-local --env-file .env.local -p 8000:8000 dewey-mcp:local
```

Use `.env` instead of `.env.local` if that is where your local settings live.
`--env-file` passes values into the running container process; it does not bake
secrets into the image.

In another terminal, verify that the container is listening and that Azure
Search is reachable:

```bash
curl http://127.0.0.1:8000/livez
curl http://127.0.0.1:8000/readyz
```

`/livez` should return `{"status":"ok"}` when the server process is running.
`/readyz` should return `{"status":"ready","providers":...}` when the required
configuration is loaded and both Azure Search provider probes succeed. It
returns `503` with per-provider details when either archive is unavailable.

Follow container logs while testing:

```bash
docker logs -f dewey-mcp-local
```

Stop the preflight container from another terminal:

```bash
docker stop dewey-mcp-local
```

If port `8000` is already in use locally, map a different host port while still
leaving the container port at `8000`:

```bash
docker run --rm --name dewey-mcp-local --env-file .env.local -p 8080:8000 dewey-mcp:local
curl http://127.0.0.1:8080/livez
curl http://127.0.0.1:8080/readyz
```

For Azure Container App parity, confirm the image listens on container port
`8000`, the MCP endpoint is `/mcp`, the liveness endpoint is `/livez`, and the
readiness endpoint is `/readyz` unless the matching environment variables
override those defaults. The Container App must provide
`AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX_NAME`,
`AZURE_SEARCH_SEMANTIC_CONFIGURATION`, `AZURE_IMAGE_SEARCH_INDEX_NAME`, and
`AZURE_IMAGE_SEARCH_SEMANTIC_CONFIGURATION`. Local API-key authentication is the
simplest preflight path; if `AZURE_SEARCH_API_KEY` is omitted, the container uses
default Azure credentials, which usually need additional local credential setup
outside Azure.

If the container exits with invalid configuration, check the required Azure
Search settings for both archives. If `/livez` succeeds but `/readyz` returns
`503`, the process is running but Azure Search configuration, authentication,
network access, or provider readiness is failing.

## MCP client configuration

Dewey exposes MCP over streamable HTTP at `MCP_PATH`, which defaults to `/mcp`.
With the default host and port, clients should connect to:

```text
http://127.0.0.1:8000/mcp
```

Do not configure Dewey as a stdio MCP command unless a separate stdio entrypoint
has been added. If a client shows no tools, first confirm the server starts with
the required Azure settings loaded and that the client is using streamable HTTP
against the `/mcp` endpoint.
