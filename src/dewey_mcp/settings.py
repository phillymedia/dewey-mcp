"""Environment-backed settings."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    mcp_host: str = Field(default="0.0.0.0", alias="MCP_HOST")
    mcp_port: int = Field(default=8000, alias="MCP_PORT")
    mcp_path: str = Field(default="/mcp", alias="MCP_PATH")
    health_liveness_path: str = Field(default="/livez", alias="HEALTH_LIVENESS_PATH")
    health_readiness_path: str = Field(default="/readyz", alias="HEALTH_READINESS_PATH")

    search_provider: Literal["azure"] = Field(default="azure", alias="SEARCH_PROVIDER")
    search_provider_timeout_seconds: float = Field(
        default=10.0,
        alias="SEARCH_PROVIDER_TIMEOUT_SECONDS",
        gt=0,
    )

    azure_search_endpoint: str = Field(alias="AZURE_SEARCH_ENDPOINT")
    azure_search_index_name: str = Field(alias="AZURE_SEARCH_INDEX_NAME")
    azure_search_semantic_configuration: str = Field(
        alias="AZURE_SEARCH_SEMANTIC_CONFIGURATION"
    )
    azure_search_api_key: SecretStr | None = Field(
        default=None,
        alias="AZURE_SEARCH_API_KEY",
    )

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be a valid Python logging level")
        return normalized
