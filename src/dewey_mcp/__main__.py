"""Command-line entrypoint."""

from __future__ import annotations

from pydantic import ValidationError

from dewey_mcp.logging import configure_logging
from dewey_mcp.server import create_mcp
from dewey_mcp.settings import Settings


def main() -> None:
    settings = Settings()
    configure_logging(settings.log_level)
    mcp = create_mcp(settings)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    try:
        main()
    except ValidationError as exc:
        raise SystemExit(f"Invalid configuration: {exc}") from exc
