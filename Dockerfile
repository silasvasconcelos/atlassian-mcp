FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md /app/
COPY src /app/src
COPY scripts /app/scripts
COPY openapi /app/openapi

RUN uv sync --frozen --no-dev \
    && chmod +x /app/scripts/start_server.sh

EXPOSE 8000

ENV MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    MCP_LOG_LEVEL=INFO

CMD ["/app/scripts/start_server.sh"]
