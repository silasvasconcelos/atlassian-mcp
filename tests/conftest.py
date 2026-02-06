import os
from pathlib import Path

import pytest

from dotenv import load_dotenv


def pytest_configure(config):
    for name in (".dev.test", ".env.test"):
        env_path = Path(name)
        if env_path.exists():
            load_dotenv(env_path, override=True)


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests against real Jira",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return
    skip_marker = pytest.mark.skip(reason="Need --run-integration to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    skipped = terminalreporter.stats.get("skipped", [])
    if not skipped:
        return
    terminalreporter.write_line("")
    terminalreporter.write_line("Skipped tests summary:")
    for report in skipped:
        reason = getattr(report, "longrepr", None)
        if hasattr(reason, "reprcrash"):
            detail = reason.reprcrash.message
        elif reason:
            detail = str(reason)
        else:
            detail = "No reason provided"
        terminalreporter.write_line(f"- {report.nodeid}: {detail}")
