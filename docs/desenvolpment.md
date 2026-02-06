# Desenvolvimento

## Requisitos

- Python 3.10+

## Instalação (uv)

```bash
uv venv
source .venv/bin/activate
uv sync
```

## Instalação (pip)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Baixar o OpenAPI

Este projeto não inclui o arquivo `swagger-v3.v3.json` para evitar check-ins enormes e manter a fonte oficial como verdade.
Baixe o spec com o script:

```bash
python scripts/update_openapi.py
```

Isso salva em `openapi/swagger-v3.v3.json` (o path pode ser sobrescrito por `JIRA_OPENAPI_PATH`).

## Testes

```bash
uv sync --extra dev
uv run pytest
```

### Alternativa com pip

```bash
pip install -e ".[dev]"
pytest
```
