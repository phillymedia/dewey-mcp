# Configure Azure Search Through Environment Variables

Dewey MCP receives Azure AI Search configuration through environment variables so the same container image can run against different environments without rebuilds. Required Azure search settings should be validated at startup and missing configuration should fail fast instead of surfacing later during a tool call.

Expected settings include the Azure Search endpoint, index name, semantic configuration, and authentication configuration. Provider-specific index field mappings are code-defined rather than environment-defined.

The gateway supports both Azure Search API key authentication and Azure identity authentication. An injected API key is acceptable for local development and non-Azure deployment targets; managed identity or default Azure credentials are preferred where the container runtime supports them.
