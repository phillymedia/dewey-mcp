# Use Streamable HTTP Transport

Dewey MCP exposes MCP over streamable HTTP as its only production transport. The server is intended to run as a containerized service for remote agents, so the production entrypoint should bind to a configurable host and port rather than relying on stdio child-process execution.
