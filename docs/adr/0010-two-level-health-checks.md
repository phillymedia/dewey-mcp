# Use Two-Level Health Checks

Dewey MCP exposes two levels of health checks for container operation: liveness verifies that the server process is running, and readiness verifies that required configuration is loaded and both search providers can respond to lightweight probes. An outage of either the News Archive or Image Archive provider should make the service unready without confusing that state with a crashed process.
