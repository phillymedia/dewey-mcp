# Return Structured Tool Errors

Dewey MCP returns structured tool errors for validation and provider failures instead of embedding failures as fake Search Results or empty successful responses. An empty result set means the search succeeded and found no matching Article Chunks; provider failures remain explicit errors with stable, non-secret messages.
