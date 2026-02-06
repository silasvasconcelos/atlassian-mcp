SHELL := /bin/bash

PYTHON ?= python
UV ?= uv
VENV ?= .venv

.PHONY: help venv install dev openapi run test clean

help:
	@echo "Available targets:"
	@echo "  venv     - Create virtual environment with uv"
	@echo "  install  - Install package (editable)"
	@echo "  dev      - Install dev dependencies"
	@echo "  openapi  - Download Jira OpenAPI spec"
	@echo "  run      - Run MCP server"
	@echo "  test     - Run tests"
	@echo "  clean    - Remove venv and caches"

venv:
	$(UV) venv

install:
	$(UV) sync

dev:
	$(UV) sync --extra dev

openapi:
	$(UV) run $(PYTHON) scripts/update_openapi.py

run:
	$(UV) run $(PYTHON) -m jira_mcp.server

test:
	$(UV) run pytest

clean:
	rm -rf $(VENV) .pytest_cache __pycache__ .mypy_cache
