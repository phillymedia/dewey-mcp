# Use a src Package Layout

Dewey MCP moves real application code out of the root `main.py` scaffold and into an importable `src/dewey_mcp/` package. This supports production maintenance by keeping MCP registration, settings, models, provider adapters, filter translation, errors, and tests in explicit modules instead of growing the uv initialization stub into the application.
