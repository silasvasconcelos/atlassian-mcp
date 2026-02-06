from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class JiraConfig:
    base_url: str | None
    openapi_path: str


def _normalize_base_url(url: str) -> str:
    if url.endswith("/rest/api/3"):
        return url
    return url.rstrip("/") + "/rest/api/3"


def load_config() -> JiraConfig:
    base_url = os.getenv("JIRA_BASE_URL")
    openapi_path = os.getenv(
        "JIRA_OPENAPI_PATH", os.path.join("openapi", "swagger-v3.v3.json")
    )

    if base_url:
        base_url = _normalize_base_url(base_url)

    return JiraConfig(
        base_url=base_url,
        openapi_path=openapi_path,
    )
