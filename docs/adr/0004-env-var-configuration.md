# ADR 0004: Configure Azure Search Through Environment Variables

**Status:** Accepted

## Context

The same container image must run in local, test, and production environments without rebuilding environment-specific values into it. Missing provider configuration should fail at startup rather than during an agent's search.

## Decision

Dewey reads runtime configuration from environment variables using validated Pydantic settings. Required values include the Azure endpoint, News Archive index, Image Archive index, and News Archive semantic configuration.

Authentication supports an explicit Azure Search API key or `DefaultAzureCredential`. Managed identity or another default Azure credential is preferred where the hosting environment supports it. Provider field mappings remain code-defined rather than environment-defined.

## Consequences

- One immutable image can be configured for multiple environments.
- Invalid or missing required configuration prevents startup.
- Deployments must inject all required values and protect credentials outside the image.
- Schema mapping changes require code and tests rather than configuration edits.

## Related documentation

- [Configuration reference](../operations.md#configuration-reference)
- [Getting started](../getting-started.md#configure-local-access)
