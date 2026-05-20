"""
FastMCP quickstart example.

Run from the repository root:
    uv run examples/snippets/servers/fastmcp_quickstart.py
"""

from mcp.server.fastmcp import FastMCP
import json

# Create an MCP server
mcp = FastMCP("Demo", json_response=True)


# Add an addition tool
@mcp.tool()
def search_archive(search_query: str) -> int:
    """Add two numbers"""
    return json.loads({})


# Run with streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")