# Getting Started

This guide takes a new contributor from a fresh checkout to a running Dewey MCP server. You do not need Azure credentials to run the test suite, but you do need access to both Azure AI Search indexes to run the service.

## Prerequisites

Install:

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- Git

For live searches, obtain the Azure Search endpoint, News Archive index name, Image Archive index name, semantic configuration name, and either an API key or a working Azure identity.

## Install the project

From the repository root, install the runtime and development dependencies locked in `uv.lock`:

```bash
uv sync --dev
```

Confirm the checkout is healthy before adding local configuration:

```bash
uv run pytest
uv run ruff check src tests main.py
uv run black --check src tests main.py
```

The tests use fake providers by default, so these commands require neither Azure credentials nor network access. The optional experimental notebooks are outside the application lint and format checks.

## Configure local access

Copy the environment template:

```bash
cp .env.template .env
```

Set these required values:

```text
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_INDEX_NAME=
AZURE_IMAGE_SEARCH_INDEX_NAME=
AZURE_SEARCH_SEMANTIC_CONFIGURATION=
```

For API-key authentication, also set `AZURE_SEARCH_API_KEY`. If it is empty or omitted, the Azure SDK uses `DefaultAzureCredential`, which can resolve credentials from supported local tools or managed identity.

Dewey automatically reads `.env`; it does not automatically read `.env.local`. See [Environment loading](operations.md#environment-loading) if your secrets are already in `.env.local`.

Never commit either file. Both are ignored by Git.

## Run the server

Start Dewey from the repository root:

```bash
uv run dewey-mcp
```

The process validates configuration before starting. With the defaults, it exposes:

| Endpoint | Purpose |
| --- | --- |
| `http://127.0.0.1:8000/mcp` | Streamable HTTP MCP endpoint |
| `http://127.0.0.1:8000/livez` | Process liveness |
| `http://127.0.0.1:8000/readyz` | Both Azure index probes |

In another terminal, check the service:

```bash
curl http://127.0.0.1:8000/livez
curl http://127.0.0.1:8000/readyz
```

Successful responses are `{"status":"ok"}` and `{"status":"ready"}` respectively.

## Connect an MCP client

Configure the client for streamable HTTP at:

```text
http://127.0.0.1:8000/mcp
```

Dewey does not offer a stdio transport. After connecting, the client should discover `search_archive` and `search_image_archive`. Try a small request such as:

```json
{
  "query": "city hall",
  "limit": 3
}
```

The exact contracts and more examples are in the [tool reference](tool-reference.md).

## Common setup problems

### The process exits immediately

Read the `Invalid configuration` message. All four Azure Search settings are required, including `AZURE_IMAGE_SEARCH_INDEX_NAME`.

### `/livez` works but `/readyz` returns 503

The server is running, but at least one index probe failed. Check both index names, the endpoint, credentials, network access, and the configured timeout.

### The client discovers no tools

Confirm that the client uses streamable HTTP, not stdio, and that its URL includes the configured MCP path (`/mcp` by default).

### Port 8000 is already in use

Set a different `MCP_PORT` in `.env`, restart Dewey, and update the client and health-check URLs.

For container and deployment failures, continue with the [operations guide](operations.md#troubleshooting).

## Next steps

Read the [domain language](../CONTEXT.md), then follow a request through the system in the [architecture guide](architecture.md).
