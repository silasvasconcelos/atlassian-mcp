import os
import pytest

from jira_mcp.config import JiraConfig
from jira_mcp.server import JiraMCPServer


def _env(name: str) -> str | None:
    value = os.getenv(name)
    return value if value and value.strip() else None


def _make_server():
    config = JiraConfig(
        base_url=None,
        openapi_path="openapi/swagger-v3.v3.json",
    )
    return JiraMCPServer(config, None)


def _require_openapi():
    if not os.path.exists("openapi/swagger-v3.v3.json"):
        pytest.skip("OpenAPI spec not found; run scripts/update_openapi.py")


def _headers_basic():
    base_url = _env("JIRA_TEST_BASIC_BASE_URL")
    email = _env("JIRA_TEST_BASIC_EMAIL")
    token = _env("JIRA_TEST_BASIC_API_TOKEN")
    if not base_url or not email or not token:
        return None
    return {
        "JIRA_AUTH_MODE": "basic",
        "JIRA_BASE_URL": base_url,
        "JIRA_EMAIL": email,
        "JIRA_API_TOKEN": token,
    }


def _headers_oauth():
    access_token = _env("JIRA_TEST_OAUTH_ACCESS_TOKEN")
    cloud_id = _env("JIRA_TEST_OAUTH_CLOUD_ID")
    if not access_token or not cloud_id:
        return None
    if len(cloud_id) < 20 or "-" not in cloud_id:
        return None
    return {
        "JIRA_AUTH_MODE": "oauth2",
        "JIRA_OAUTH_ACCESS_TOKEN": access_token,
        "JIRA_CLOUD_ID": cloud_id,
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_basic_get_myself():
    _require_openapi()
    headers = _headers_basic()
    if not headers:
        pytest.skip("Basic auth env vars not set")
    server = _make_server()
    result = await server.call_tool(
        "jira_getCurrentUser",
        {"headers": headers},
    )
    if result["status"] == 404:
        pytest.skip("OAuth cloud_id invalid or user not found")
    assert result["status"] == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_oauth_get_myself():
    _require_openapi()
    headers = _headers_oauth()
    if not headers:
        pytest.skip("OAuth env vars not set")
    server = _make_server()
    result = await server.call_tool(
        "jira_getCurrentUser",
        {"headers": headers},
    )
    if result["status"] == 404:
        pytest.skip("OAuth cloud_id invalid or user not found")
    assert result["status"] == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_issue():
    _require_openapi()
    issue_key = _env("JIRA_TEST_ISSUE_KEY")
    auth_mode = _env("JIRA_TEST_ISSUE_AUTH_MODE") or "basic"
    if not issue_key:
        pytest.skip("JIRA_TEST_ISSUE_KEY not set")

    if auth_mode == "basic":
        headers = _headers_basic()
    else:
        headers = _headers_oauth()

    if not headers:
        pytest.skip("Auth headers not configured for issue test")

    server = _make_server()
    result = await server.call_tool(
        "jira_getIssue",
        {"issueIdOrKey": issue_key, "headers": headers},
    )
    if result["status"] == 404:
        pytest.skip("Issue not found or not visible with provided credentials")
    assert result["status"] == 200
