import asyncio

import httpx
import respx

from jira_mcp.client import JiraClient
from jira_mcp.config import JiraConfig


def test_request_building_basic_url_and_query():
    config = JiraConfig(
        base_url=None,
        openapi_path="tests/fixtures/openapi.json",
    )
    client = JiraClient(config)

    with respx.mock:
        route = respx.get(
            "https://example.atlassian.net/rest/api/3/issue/ABC-1",
            params={"expand": "names"},
        ).mock(return_value=httpx.Response(200, json={"ok": True}))

        response = asyncio.run(
            client.request(
                method="get",
                path="/rest/api/3/issue/ABC-1",
                base_url="https://example.atlassian.net",
                query={"expand": "names"},
                headers=None,
                body=None,
                content_type=None,
            )
        )

    assert route.called
    assert response.body == {"ok": True}
