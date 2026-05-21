# Use Structured Operational Logging

Dewey MCP emits structured logs for operational visibility, including fields such as request identifier, filter fields used, requested limit, result count, provider latency, and provider error category. Logs must not include returned `chunk_text`, because Search Results may contain article excerpts that should stay in tool responses rather than service logs.

Raw `search_text` is excluded from logs by default. Search logs should use metadata such as search text length, filter fields, requested limit, result count, latency, and error category.
