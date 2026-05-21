"""Provider-neutral interfaces."""

from __future__ import annotations

from typing import Protocol

from dewey_mcp.models import SearchRequest, SearchResponse


class ArchiveSearchProvider(Protocol):
    """Provider-neutral async search interface."""

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Search the News Archive."""

    async def probe(self) -> None:
        """Verify provider readiness with a lightweight operation."""

    async def close(self) -> None:
        """Release provider resources."""
