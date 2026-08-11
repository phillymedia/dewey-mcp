# Operations

This guide covers runtime configuration, containers, deployment, health, logging, and incident diagnosis. For a first local run, begin with [Getting Started](getting-started.md).

## Configuration reference

Dewey reads environment variables through Pydantic settings and fails before startup when a required value is missing or invalid.

### Required settings

| Variable | Purpose |
| --- | --- |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search service endpoint shared by both providers. |
| `AZURE_SEARCH_INDEX_NAME` | News Archive index name. |
| `AZURE_IMAGE_SEARCH_INDEX_NAME` | Image Archive index name. |
| `AZURE_SEARCH_SEMANTIC_CONFIGURATION` | Semantic configuration used by News Archive search. |

`AZURE_IMAGE_SEARCH_INDEX_NAME` has no application default. The example name used in tests is not a runtime default.

### Optional settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `AZURE_SEARCH_API_KEY` | unset | API key; when absent, use `DefaultAzureCredential`. |
| `LOG_LEVEL` | `INFO` | Python log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `MCP_HOST` | `0.0.0.0` | HTTP bind address. |
| `MCP_PORT` | `8000` | HTTP listen port. |
| `MCP_PATH` | `/mcp` | Streamable HTTP MCP path. |
| `HEALTH_LIVENESS_PATH` | `/livez` | Liveness route. |
| `HEALTH_READINESS_PATH` | `/readyz` | Readiness route. |
| `SEARCH_PROVIDER` | `azure` | Provider selection; only `azure` is currently accepted. |
| `SEARCH_PROVIDER_TIMEOUT_SECONDS` | `10` | Positive timeout for a complete provider operation. |

`OPENAI_API_KEY` appears in `.env.template` only for optional notebook experiments. The Dewey service ignores it.

Azure index field mappings are fixed in the provider adapters. Changing a mapping is a code and test change, not an environment configuration change.

## Environment loading

The service automatically reads a root `.env` file. Shell environment variables take precedence. It does not automatically read `.env.local`.

To use `.env.local`, export it into the current shell before starting Dewey:

```bash
set -a
source .env.local
set +a
uv run dewey-mcp
```

Keep credentials out of Git. Use an API key only where necessary; prefer managed identity or another `DefaultAzureCredential` source in Azure-hosted environments.

## Health checks

| Route | Success | Failure meaning |
| --- | --- | --- |
| `/livez` | `200 {"status":"ok"}` | No application-specific failure path; loss of response usually means the process or route is unavailable. |
| `/readyz` | `200 {"status":"ready"}` | `503` means the News Archive or Image Archive probe failed or timed out. |

Readiness probes both Azure indexes with `get_document_count`. It does not execute a representative search. A failure of either provider makes the whole service unready.

If route paths are overridden, update platform probes and runbooks at the same time.

## Structured logs

Logs are JSON on standard error and are intended for container aggregation. Useful fields include:

- `timestamp`, `level`, `logger`, and event `message`
- Search Text length and selected filter names
- requested limit and returned result count
- request and provider latency
- stable error category

Raw Search Text, returned Article Chunk text, image descriptions, credentials, and provider exception details must not be logged.

## Docker preflight

Build the production image:

```bash
docker build -t dewey-mcp:local .
```

Run it with local settings:

```bash
docker run --rm --name dewey-mcp-local --env-file .env.local -p 8000:8000 dewey-mcp:local
```

Use `.env` instead if that is your configured file. `--env-file` passes values to the container process; it does not bake them into the image.

In another terminal:

```bash
curl http://127.0.0.1:8000/livez
curl http://127.0.0.1:8000/readyz
docker logs -f dewey-mcp-local
```

Stop the container with:

```bash
docker stop dewey-mcp-local
```

If host port 8000 is occupied, use `-p 8080:8000` and make requests to port 8080.

The production image installs locked runtime dependencies only, runs as a non-root `appuser`, and listens on container port 8000 by default.

## Deployment

Every push to `main` runs the Azure-generated workflow in `.github/workflows/`. The workflow:

1. checks out the repository;
2. authenticates to Azure using GitHub OIDC;
3. builds the Docker image and pushes a commit-SHA tag to Azure Container Registry; and
4. deploys that image to the `app-dewey-mcp` Container App in resource group `dewey-mcp-aca-env`.

The workflow can also be run manually with `workflow_dispatch`.

Merging to `main` is therefore a production deployment. Before merging, complete the [contributor checks](contributing.md#required-checks) and the Docker preflight above.

Runtime settings belong on the Container App, not in the image or workflow. GitHub repository secrets hold the Azure OIDC identifiers and registry credentials used by the workflow.

After deployment, verify `/livez`, `/readyz`, MCP tool discovery, and one low-cost search against each archive.

## Access control

Dewey does not authenticate MCP clients. Production deployments must enforce access through private networking, a gateway, Azure platform authentication, or an equivalent infrastructure control. Do not expose the MCP endpoint publicly without that protection.

## Troubleshooting

### Container exits during startup

Inspect the configuration validation error. Confirm all four required settings exist in the container environment and that `LOG_LEVEL`, `SEARCH_PROVIDER`, ports, and timeout values are valid.

### Liveness passes but readiness fails

The process is healthy but one provider probe failed. Check both index names, Azure endpoint reachability, credentials and role assignments, service firewalls, and the timeout. The readiness error intentionally does not identify which provider failed, so correlate it with provider logs.

### Searches time out

Review provider latency and retry logs. The timeout covers retries as well as the final attempt. Increasing it can hide an unhealthy index, so confirm Azure latency and throttling before changing the setting.

### A search returns an unexpected field or no content

Compare the live index schema with the code-defined mappings in `providers/azure.py` and `providers/azure_image.py`. Do not try to fix schema drift with environment variables.

### An MCP client cannot connect

Confirm the host port, `MCP_PATH`, and streamable HTTP transport. Then verify that infrastructure access controls allow the client to reach the endpoint.
