import json
from pathlib import Path

from jira_mcp.tools import build_operations


def test_build_operations_from_fixture():
    spec = json.loads(Path("tests/fixtures/openapi.json").read_text(encoding="utf-8"))
    operations = build_operations(spec)
    names = {op.name for op in operations}
    assert names == {"jira_getIssue", "jira_createIssue"}
