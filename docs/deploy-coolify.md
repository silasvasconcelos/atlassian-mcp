# Deploy no Coolify

## Estrategia de deploy

Este projeto usa deploy via `Dockerfile` (Build Pack = Dockerfile).

## Configuracao no Coolify

1. Crie um novo recurso apontando para este repositorio.
2. Em **Build Pack**, selecione **Dockerfile**.
3. Porta da aplicacao: `8000`.
4. Healthcheck path: `/health`.
5. Branch: a branch que voce deseja publicar.

## Variaveis de ambiente recomendadas

- `MCP_HOST=0.0.0.0`
- `MCP_PORT=8000`
- `MCP_LOG_LEVEL=INFO`
- `JIRA_OPENAPI_URL` (opcional; default oficial da Atlassian)
- `JIRA_OPENAPI_PATH` (opcional; default `openapi/swagger-v3.v3.json`)

## Observacoes

- O container baixa automaticamente o OpenAPI (`swagger-v3.v3.json`) no boot se o arquivo nao existir.
- Endpoint de healthcheck: `GET /health` com resposta esperada `ok`.
