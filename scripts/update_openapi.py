from __future__ import annotations

import os
from pathlib import Path

import httpx

DEFAULT_URL = "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json"


def main() -> None:
    url = os.getenv("JIRA_OPENAPI_URL", DEFAULT_URL)
    target = Path("openapi") / "swagger-v3.v3.json"
    target.parent.mkdir(parents=True, exist_ok=True)

    response = httpx.get(url, timeout=60.0)
    response.raise_for_status()

    target.write_text(response.text, encoding="utf-8")
    print(f"Saved OpenAPI spec to {target}")


if __name__ == "__main__":
    main()
