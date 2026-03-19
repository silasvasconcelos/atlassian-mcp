#!/usr/bin/env sh
set -eu

OPENAPI_PATH="${JIRA_OPENAPI_PATH:-openapi/swagger-v3.v3.json}"

if [ ! -f "$OPENAPI_PATH" ]; then
  echo "OpenAPI spec not found at $OPENAPI_PATH. Downloading..."
  python scripts/update_openapi.py
fi

exec python -m jira_mcp.server
