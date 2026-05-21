# Use a Non-root Production Container

Dewey MCP's production Docker image runs the service as a non-root user, exposes only the configured MCP HTTP port, and installs only runtime dependencies by default. The image should be deployable in locked-down container platforms without requiring root permissions or a writable application directory.
