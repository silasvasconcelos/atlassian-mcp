import json
from pathlib import Path

from jira_mcp.tools import build_operations


def _get_op(name: str):
    spec = json.loads(Path("tests/fixtures/openapi.json").read_text(encoding="utf-8"))
    operations = build_operations(spec)
    for op in operations:
        if op.name == name:
            return op
    raise AssertionError(f"Missing operation {name}")


def test_get_issue_schema():
    op = _get_op("jira_getIssue")
    schema = op.input_schema
    assert "issueIdOrKey" in schema["properties"]
    assert "expand" in schema["properties"]
    assert "X-Atlassian-Token" in schema["properties"]
    assert "headers" in schema["properties"]
    assert "issueIdOrKey" in schema.get("required", [])
    assert "body" not in schema["properties"]


def test_create_issue_schema_body_required():
    op = _get_op("jira_createIssue")
    schema = op.input_schema
    assert "body" in schema["properties"]
    assert "body" in schema.get("required", [])
