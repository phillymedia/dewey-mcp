"""Provider-neutral interfaces."""

from __future__ import annotations

from typing import Protocol

from dewey_mcp.models import (
    ImageSearchRequest,
    ImageSearchResponse,
    SearchRequest,
    SearchResponse,
)


class SearchProviderLifecycle(Protocol):
    """Lifecycle operations shared by search providers."""

    async def probe(self) -> None:
        """Verify provider readiness with a lightweight operation."""

    async def close(self) -> None:
        """Release provider resources."""


class ArchiveSearchProvider(SearchProviderLifecycle, Protocol):
    """Provider-neutral async search interface."""

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Search the News Archive."""


class ImageSearchProvider(SearchProviderLifecycle, Protocol):
    """Provider-neutral async Image Archive search interface."""

    async def search(self, request: ImageSearchRequest) -> ImageSearchResponse:
        """Search the Image Archive."""
