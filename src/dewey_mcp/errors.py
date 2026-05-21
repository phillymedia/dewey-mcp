"""Application error types."""

from __future__ import annotations


class DeweyMcpError(Exception):
    """Base exception for Dewey MCP errors."""

    code = "dewey_mcp_error"
    public_message = "Dewey MCP could not complete the request."

    def to_tool_error(self) -> dict[str, str]:
        return {"error": self.code, "message": self.public_message}


class SearchProviderError(DeweyMcpError):
    """Raised when the configured search provider cannot satisfy a request."""

    code = "search_provider_unavailable"
    public_message = "The archive search provider did not respond successfully."


class SearchProviderTimeoutError(SearchProviderError):
    """Raised when the search provider exceeds the configured operation budget."""

    code = "search_provider_timeout"
    public_message = "The archive search provider timed out."
