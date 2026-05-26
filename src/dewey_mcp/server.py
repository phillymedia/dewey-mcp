"""FastMCP server assembly."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from time import monotonic
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent
from pydantic import Field, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from dewey_mcp.errors import DeweyMcpError, SearchProviderError
from dewey_mcp.models import (
    DEFAULT_SEARCH_LIMIT,
    SearchRequest,
    SearchResponse,
)
from dewey_mcp.ports import ArchiveSearchProvider
from dewey_mcp.providers.factory import build_search_provider
from dewey_mcp.settings import Settings

LOGGER = logging.getLogger(__name__)


def create_mcp(
    settings: Settings,
    search_provider: ArchiveSearchProvider | None = None,
) -> FastMCP:
    """Create the configured FastMCP server."""

    provider = search_provider or build_search_provider(settings)

    mcp = FastMCP(
        "Dewey MCP",
        host=settings.mcp_host,
        port=settings.mcp_port,
        streamable_http_path=settings.mcp_path,
        json_response=True,
        log_level=settings.log_level,
        lifespan=_provider_lifespan(provider),
    )

    @mcp.tool(structured_output=False)
    async def search_archive(
        query: Annotated[
            str,
            Field(description="Required search query. Use '*' to search everything."),
        ],
        start_date: Annotated[
            date | None,
            Field(description="Inclusive lower bound for publish_date (YYYY-MM-DD)."),
        ] = None,
        end_date: Annotated[
            date | None,
            Field(description="Inclusive upper bound for publish_date (YYYY-MM-DD)."),
        ] = None,
        authors: Annotated[
            list[str] | None,
            Field(description="Optional list of authors; results match any one."),
        ] = None,
        limit: Annotated[
            int,
            Field(
                ge=1,
                le=20,
                description="Maximum number of Article Chunks to return.",
            ),
        ] = DEFAULT_SEARCH_LIMIT,
    ) -> CallToolResult:
        """Search the News Archive and return matching Article Chunks."""

        request_started = monotonic()
        try:
            request = SearchRequest(
                query=query,
                start_date=start_date,
                end_date=end_date,
                authors=authors,
                limit=limit,
            )
            response = await provider.search(request)
            LOGGER.info(
                "search_archive_completed",
                extra={
                    "query_length": len(request.query),
                    "filter_fields": _request_filter_fields(request),
                    "requested_limit": request.limit,
                    "result_count": response.count,
                    "latency_ms": round((monotonic() - request_started) * 1000, 2),
                },
            )
            return _success_tool_result(response)
        except ValidationError:
            raise
        except DeweyMcpError as exc:
            LOGGER.warning(
                "search_archive_failed",
                extra={
                    "error": exc.code,
                    "latency_ms": round((monotonic() - request_started) * 1000, 2),
                },
            )
            return _error_tool_result(exc)

    @mcp.custom_route(settings.health_liveness_path, methods=["GET"])
    async def liveness(_: Request) -> Response:
        return JSONResponse({"status": "ok"})

    @mcp.custom_route(settings.health_readiness_path, methods=["GET"])
    async def readiness(_: Request) -> Response:
        try:
            await provider.probe()
        except SearchProviderError as exc:
            return JSONResponse(
                {"status": "unready", **exc.to_tool_error()},
                status_code=503,
            )
        return JSONResponse({"status": "ready"})

    return mcp


def _request_filter_fields(request: SearchRequest) -> list[str]:
    fields: list[str] = []
    if request.start_date is not None or request.end_date is not None:
        fields.append("published_date")
    if request.authors:
        fields.append("authors")
    return fields


def _success_tool_result(response: SearchResponse) -> CallToolResult:
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=response.model_dump_json(),
            )
        ],
        structuredContent=response.model_dump(mode="json"),
    )


def _error_tool_result(error: DeweyMcpError) -> CallToolResult:
    payload = error.to_tool_error()
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"{payload['error']}: {payload['message']}",
            )
        ],
        structuredContent=payload,
        isError=True,
    )


def _provider_lifespan(
    provider: ArchiveSearchProvider,
):
    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await provider.close()

    return lifespan
