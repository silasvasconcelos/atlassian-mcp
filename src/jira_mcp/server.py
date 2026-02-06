from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from dotenv import load_dotenv

from mcp.server.lowlevel import Server
import base64
import contextlib

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.fastmcp.server import StreamableHTTPASGIApp
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.types import Resource, Tool, ResourcesCapability, ServerCapabilities, ToolsCapability

from .client import JiraClient
from .config import JiraConfig, load_config
from .openapi_loader import OpenAPILoadError, load_openapi
from .tools import Operation, build_operations


class JiraMCPServer:
    def __init__(self, config: JiraConfig, mcp_server: Server | None = None) -> None:
        self._config = config
        self._client = JiraClient(config)
        self._mcp_server = mcp_server
        spec = load_openapi(config.openapi_path)
        self._operations = build_operations(spec)
        self._tool_map = {op.name: op for op in self._operations}

    def list_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        for op in self._operations:
            tools.append(
                Tool(
                    name=op.name,
                    description=op.description,
                    inputSchema=op.input_schema,
                )
            )
        return tools

    def list_resources(self) -> list[Resource]:
        return [
            Resource(
                uri="config://jira",
                name="Jira MCP config",
                description="Resolved Jira MCP configuration (secrets omitted).",
                mimeType="application/json",
            )
        ]

    def read_resource(self, uri: str) -> str:
        if uri != "config://jira":
            raise ValueError(f"Unknown resource: {uri}")
        safe = {
            "base_url": self._config.base_url,
            "openapi_path": self._config.openapi_path,
        }
        return json.dumps(safe, indent=2)

    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
        if name not in self._tool_map:
            raise ValueError(f"Unknown tool: {name}")
        op = self._tool_map[name]
        args = arguments or {}
        logging.getLogger("jira_mcp").debug("Calling tool %s", name)

        missing = [key for key in op.required_params if key not in args]
        if missing:
            raise ValueError(f"Missing required arguments: {', '.join(sorted(missing))}")

        path_params = {key: args[key] for key in op.path_params if key in args}
        query_params = {key: args[key] for key in op.query_params if key in args}
        header_params = {key: str(args[key]) for key in op.header_params if key in args}

        extra_headers: dict[str, str] = {}
        try:
            request = self._mcp_server.request_context.request if self._mcp_server else None
            if request is not None:
                extra_headers.update({k: v for k, v in request.headers.items()})
        except Exception:
            pass

        tool_headers = args.get("headers") or {}
        if not isinstance(tool_headers, dict):
            raise ValueError("headers must be an object with string values")

        # Only tool-provided headers are forwarded to Jira.
        # Request headers are used for config only.
        forward_headers = {str(k): str(v) for k, v in tool_headers.items()}

        def _normalize_header_key(key: str) -> str:
            return key.replace("-", "_").upper()

        combined_headers = dict(extra_headers)
        combined_headers.update(tool_headers)
        config_headers = {_normalize_header_key(k): str(v) for k, v in combined_headers.items()}
        auth_mode = config_headers.get("JIRA_AUTH_MODE")
        base_url = config_headers.get("JIRA_BASE_URL") or self._config.base_url

        if not auth_mode:
            logging.getLogger("jira_mcp").error("Missing JIRA_AUTH_MODE in headers")
            raise ValueError("JIRA_AUTH_MODE is required in headers")

        auth_mode = auth_mode.lower()
        def _strip_rest_api(url: str) -> str:
            suffix = "/rest/api/3"
            return url[: -len(suffix)] if url.endswith(suffix) else url

        if auth_mode == "basic":
            email = config_headers.get("JIRA_EMAIL")
            token = config_headers.get("JIRA_API_TOKEN")
            if not email or not token:
                logging.getLogger("jira_mcp").error("Missing JIRA_EMAIL/JIRA_API_TOKEN in headers")
                raise ValueError("JIRA_EMAIL and JIRA_API_TOKEN are required in headers")
            encoded = base64.b64encode(f"{email}:{token}".encode("utf-8")).decode("ascii")
            auth_header = {"Authorization": f"Basic {encoded}"}
            if not base_url:
                raise ValueError("JIRA_BASE_URL is required in headers for basic auth")
            base_url = _strip_rest_api(base_url)
        elif auth_mode == "oauth2":
            access_token = config_headers.get("JIRA_OAUTH_ACCESS_TOKEN")
            cloud_id = config_headers.get("JIRA_CLOUD_ID")
            if not access_token:
                logging.getLogger("jira_mcp").error("Missing JIRA_OAUTH_ACCESS_TOKEN in headers")
                raise ValueError("JIRA_OAUTH_ACCESS_TOKEN is required in headers")
            if not cloud_id and base_url and "api.atlassian.com/ex/jira/" in base_url:
                base_url = _strip_rest_api(base_url)
            else:
                if not cloud_id:
                    logging.getLogger("jira_mcp").error("Missing JIRA_CLOUD_ID in headers for oauth2")
                    raise ValueError("JIRA_CLOUD_ID is required in headers for oauth2")
                base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}"
            auth_header = {"Authorization": f"Bearer {access_token}"}
        else:
            raise ValueError("JIRA_AUTH_MODE must be 'basic' or 'oauth2'")

        if not base_url:
            logging.getLogger("jira_mcp").error("Missing JIRA_BASE_URL in headers")
            raise ValueError("JIRA_BASE_URL is required")

        resolved_base_url = base_url.rstrip("/")

        blocked = {"content-length", "host", "connection", "transfer-encoding"}
        extra_headers_clean = {
            str(k): str(v)
            for k, v in forward_headers.items()
            if not _normalize_header_key(str(k)).startswith("JIRA_")
            and str(k).lower() not in blocked
        }

        header_params.update(extra_headers_clean)
        header_params.update(auth_header)
        body = args.get("body") if "body" in args else None

        try:
            path = op.path.format(**path_params)
        except KeyError as exc:
            raise ValueError(f"Missing path parameter: {exc.args[0]}") from exc

        response = await self._client.request(
            method=op.method,
            path=path,
            base_url=resolved_base_url,
            query=query_params,
            headers=header_params,
            body=body,
            content_type=op.request_body_content_type,
        )

        return {
            "status": response.status,
            "headers": response.headers,
            "body": response.body,
        }


async def _run_server() -> None:
    load_dotenv()
    log_level = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    logger = logging.getLogger("jira_mcp")
    config = load_config()
    mcp = Server("jira-mcp")
    jira_server = JiraMCPServer(config, mcp)

    logger.info("Jira MCP server initialized")

    @mcp.list_tools()
    async def _list_tools() -> list[Tool]:
        return jira_server.list_tools()

    @mcp.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
        return await jira_server.call_tool(name, arguments)

    @mcp.list_resources()
    async def _list_resources() -> list[Resource]:
        return jira_server.list_resources()

    @mcp.read_resource()
    async def _read_resource(uri: str) -> str:
        return jira_server.read_resource(uri)

    # Expose capabilities for MCP clients
    _ = ServerCapabilities(
        tools=ToolsCapability(),
        resources=ResourcesCapability(),
    )

    session_manager = StreamableHTTPSessionManager(mcp)

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette):
        async with session_manager.run():
            yield

    streamable_app = StreamableHTTPASGIApp(session_manager)

    class MCPPrefixApp:
        def __init__(self, app, prefix: str = "/mcp") -> None:
            self._app = app
            self._prefix = prefix.rstrip("/") if prefix != "/" else ""

        async def __call__(self, scope, receive, send) -> None:
            if scope["type"] != "http":
                return await self._app(scope, receive, send)

            path = scope.get("path", "")
            if self._prefix == "":
                return await self._app(scope, receive, send)

            if path == self._prefix or path.startswith(self._prefix + "/"):
                new_scope = dict(scope)
                new_scope["root_path"] = self._prefix
                new_scope["path"] = path[len(self._prefix):] or "/"
                return await self._app(new_scope, receive, send)

            # Not found
            await send({"type": "http.response.start", "status": 404, "headers": []})
            await send({"type": "http.response.body", "body": b"Not Found"})

    prefix_app = MCPPrefixApp(streamable_app, prefix="/mcp")
    app = Starlette(
        lifespan=lifespan,
        routes=[Mount("/", app=prefix_app)],
    )

    import uvicorn

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
    )
    uvicorn_server = uvicorn.Server(config)
    await uvicorn_server.serve()


def main() -> None:
    try:
        asyncio.run(_run_server())
    except OpenAPILoadError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
