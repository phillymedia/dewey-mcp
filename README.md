# Dewey MCP

Dewey MCP is a containerized [FastMCP](https://github.com/modelcontextprotocol/python-sdk) server that gives agents read-only search over news and image archives backed by Azure AI Search.

The service exposes two tools:

- `search_archive` returns matching excerpts from News Articles.
- `search_image_archive` returns metadata and links for Archived Images.

Dewey never ingests, updates, deletes, reindexes, downloads, or proxies archive content.

## Start here

New contributors should follow this path:

1. [Get the service running](docs/getting-started.md).
2. Learn the project's [domain language](CONTEXT.md).
3. Understand the [architecture](docs/architecture.md).
4. Read the [contribution workflow](docs/contributing.md) before making changes.

Use the [tool reference](docs/tool-reference.md) for request and response contracts. Use the [operations guide](docs/operations.md) for configuration, Docker, deployment, health checks, and troubleshooting.

## Quick start

Prerequisites: Python 3.11+, [uv](https://docs.astral.sh/uv/), and access to the project's Azure AI Search resources.

```bash
uv sync --dev
cp .env.template .env
```

Fill in the four required Azure settings in `.env`, then start the server:

```bash
uv run dewey-mcp
```

With the default configuration, MCP clients connect to `http://127.0.0.1:8000/mcp`. These checks confirm that the process is running and both search indexes are reachable:

```bash
curl http://127.0.0.1:8000/livez
curl http://127.0.0.1:8000/readyz
```

The default test suite does not require Azure credentials or network access:

```bash
uv run pytest
```

## Documentation map

| I want to... | Read |
| --- | --- |
| Set up and run Dewey locally | [Getting started](docs/getting-started.md) |
| Understand project terminology | [Domain language](CONTEXT.md) |
| Call an MCP tool or inspect its contract | [Tool reference](docs/tool-reference.md) |
| Understand the request flow and code boundaries | [Architecture](docs/architecture.md) |
| Configure, deploy, or troubleshoot the service | [Operations](docs/operations.md) |
| Change code or add a provider | [Contributing](docs/contributing.md) |
| Understand why a design choice was made | [Architecture decisions](docs/adr/README.md) |

Agent-specific repository instructions live in `AGENTS.md` and `docs/agents/`; they are not part of the contributor learning path.

## Project status

Dewey currently supports Azure AI Search, streamable HTTP transport, and snake_case MCP contracts. Merging to `main` deploys the production container automatically, so complete the checks in the [contribution workflow](docs/contributing.md) before merging.
