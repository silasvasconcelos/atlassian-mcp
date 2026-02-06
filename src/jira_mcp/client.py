from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import httpx

from .config import JiraConfig

logger = logging.getLogger("jira_mcp.http")


@dataclass
class JiraResponse:
    status: int
    headers: dict[str, str]
    body: Any


class JiraClient:
    def __init__(self, config: JiraConfig) -> None:
        self._config = config

    async def request(
        self,
        method: str,
        path: str,
        base_url: str,
        query: dict[str, Any] | None,
        headers: dict[str, str] | None,
        body: Any | None,
        content_type: str | None,
    ) -> JiraResponse:
        url = base_url.rstrip("/") + path
        req_headers: dict[str, str] = {}
        if headers:
            for key, value in headers.items():
                req_headers[key] = value
        if content_type:
            req_headers.setdefault("Content-Type", content_type)

        logger.debug("HTTP %s %s", method.upper(), url)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method.upper(),
                url=url,
                params=query or None,
                headers=req_headers,
                json=body,
            )

        try:
            parsed = response.json()
        except ValueError:
            parsed = response.text

        return JiraResponse(
            status=response.status_code,
            headers=dict(response.headers),
            body=parsed,
        )
