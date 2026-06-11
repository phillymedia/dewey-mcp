"""Provider factory."""

from __future__ import annotations

from dataclasses import dataclass

from dewey_mcp.ports import ArchiveSearchProvider, ImageSearchProvider
from dewey_mcp.providers.azure import (
    AzureArchiveSearchProvider,
    AzureImageSearchProvider,
)
from dewey_mcp.settings import Settings

ALLOWED_PROVIDER_LIST = ["azure"]


@dataclass(frozen=True)
class SearchProviders:
    """Configured search providers for all Dewey search tools."""

    archive: ArchiveSearchProvider
    images: ImageSearchProvider


def build_search_provider(settings: Settings) -> ArchiveSearchProvider:
    if settings.search_provider == "azure":
        return AzureArchiveSearchProvider.from_settings(settings)
    raise ValueError(
        f"Unsupported search provider: {settings.search_provider}. "
        f"Must be one of: {ALLOWED_PROVIDER_LIST}"
    )


def build_image_search_provider(settings: Settings) -> ImageSearchProvider:
    if settings.search_provider == "azure":
        return AzureImageSearchProvider.from_settings(settings)
    raise ValueError(
        f"Unsupported search provider: {settings.search_provider}. "
        f"Must be one of: {ALLOWED_PROVIDER_LIST}"
    )


def build_search_providers(settings: Settings) -> SearchProviders:
    if settings.search_provider == "azure":
        return SearchProviders(
            archive=AzureArchiveSearchProvider.from_settings(settings),
            images=AzureImageSearchProvider.from_settings(settings),
        )
    raise ValueError(
        f"Unsupported search provider: {settings.search_provider}. "
        f"Must be one of: {ALLOWED_PROVIDER_LIST}"
    )
