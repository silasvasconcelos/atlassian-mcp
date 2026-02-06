# Deploy na Railway

## Arquivos de deploy

- `railway.json` com `startCommand` e healthcheck em `/health`
- `Procfile` como fallback

## Variaveis de ambiente recomendadas

- `PORT` (Railway define automaticamente)
- `MCP_HOST=0.0.0.0`
- `MCP_LOG_LEVEL=INFO` ou `DEBUG`

## Healthcheck

- Endpoint: `/health`
- Resposta esperada: `ok`

## Comando de start

```
uv run python -m jira_mcp.server
```
