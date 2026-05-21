# Use FastMCP With uv and Docker

Dewey MCP is packaged as a minimal Python service using FastMCP, uv, and a Dockerfile. The initial production shape should rely on FastMCP's streamable HTTP support rather than adding a larger web framework, while keeping the codebase structured so middleware or service integrations can be added later if they become necessary.
