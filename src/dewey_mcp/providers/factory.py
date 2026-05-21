"""Provider factory."""

from __future__ import annotations

from dewey_mcp.ports import ArchiveSearchProvider
from dewey_mcp.providers.azure import AzureArchiveSearchProvider
from dewey_mcp.settings import Settings

ALLOWED_PROVIDER_LIST = ["azure"]


def build_search_provider(settings: Settings) -> ArchiveSearchProvider:
    if settings.search_provider == "azure":
        return AzureArchiveSearchProvider.from_settings(settings)
    raise ValueError(
        f"Unsupported search provider: {settings.search_provider}. "
        f"Must be one of: {ALLOWED_PROVIDER_LIST}"
    )
