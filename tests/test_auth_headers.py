import asyncio

import httpx
import respx

from jira_mcp.client import JiraClient
from jira_mcp.config import JiraConfig
from jira_mcp.server import JiraMCPServer


def test_auth_headers_from_config_headers():
    config = JiraConfig(
        base_url=None,
        openapi_path="tests/fixtures/openapi.json",
    )
    server = JiraMCPServer(config)

    with respx.mock:
        route = respx.get(
            "https://example.atlassian.net/rest/api/3/issue/ABC-1",
        ).mock(return_value=httpx.Response(200, json={"ok": True}))

        response = asyncio.run(
            server.call_tool(
                "jira_getIssue",
                {
                    "issueIdOrKey": "ABC-1",
                    "headers": {
                        "JIRA_AUTH_MODE": "basic",
                        "JIRA_EMAIL": "user@example.com",
                        "JIRA_API_TOKEN": "token",
                        "JIRA_BASE_URL": "https://example.atlassian.net",
                    },
                },
            )
        )

    assert route.called
    assert response["status"] == 200
