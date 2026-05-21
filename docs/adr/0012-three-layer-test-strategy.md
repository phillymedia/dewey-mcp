# Use Three Test Layers

Dewey MCP uses three test layers: unit tests for request validation, filter translation, limit behavior, and result mapping; MCP tool tests with a fake provider adapter for tool behavior and structured errors; and opt-in live Azure integration tests. The default test suite must not require Azure credentials or network access.
