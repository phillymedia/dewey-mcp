# Dewey MCP

Dewey MCP is a containerized FastMCP server for read-only search over a news
archive backed by Azure AI Search.

## Tool

`search_archive` accepts:

```json
{
  "search_text": "Iran hostage crisis",
  "filters": [
    {
      "field": "published_date",
      "start": "1979-11-01",
      "end": "1979-12-01"
    },
    {
      "field": "author",
      "value": "George Will"
    }
  ],
  "limit": 10
}
```

`search_text` is required. Use `*` to search everything with filters only.
Multiple filters are combined with `AND`. `limit` defaults to `10` and has a
hard maximum of `20`.

Each result is one matching article chunk:

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

## Configuration

Required:

```text
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_INDEX_NAME=
AZURE_SEARCH_SEMANTIC_CONFIGURATION=
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

The Azure index field mapping is defined in the Azure provider code, not in the
environment. The default mapping expects:

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
uv run dewey-mcp
```
