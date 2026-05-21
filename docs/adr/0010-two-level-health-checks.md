# Use Two-Level Health Checks

Dewey MCP exposes two levels of health checks for container operation: liveness verifies that the server process is running, and readiness verifies that required configuration is loaded and the search provider can respond to a lightweight probe. A provider outage should make the service unready without confusing that state with a crashed process.
