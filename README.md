# Jira MCP

Servidor MCP para Jira.

## Configuração

O usuário **não executa o MCP localmente**. Ele se conecta ao endereço onde o servidor MCP estiver publicado.

## Deploy

- Railway: veja `docs/deploy-railway.md`
- Coolify: veja `docs/deploy-coolify.md`

Se precisar alterar o host/porta do servidor:

- `MCP_HOST` (default `0.0.0.0`)
- `MCP_PORT` (default `8000`)

Para logs detalhados:

- `MCP_LOG_LEVEL=DEBUG`

## Testes de integracao (Jira real)

1. Copie `/Users/silasvasconcelos/Workspace/projects/atlassian-mcp/.env.test.example` para `.env.test` e preencha.
2. Execute:

```bash
uv run pytest --run-integration
```

## Configurar no editor (MCP client)

Este servidor expõe MCP via Streamable HTTP. Configure o client com a URL pública do serviço e envie a autenticação na própria configuração de conexão (via `headers` quando o client permitir). O servidor **não aceita** `Authorization` direto do client; ele espera os headers `JIRA_*` para montar a autenticação.

### Headers de configuração (obrigatório)

Envie os headers abaixo na conexão MCP. Eles **não** são repassados para a API do Jira; são usados apenas para montar a autenticação e a base URL.
Os nomes podem ser enviados como `JIRA_BASE_URL` ou `JIRA-BASE-URL` (hifens e underscores são aceitos).

#### Basic

- `JIRA_AUTH_MODE`: `basic`
- `JIRA_BASE_URL`: URL do seu site Jira (sem `/rest/api/3`), ex.: `https://<site>.atlassian.net`
- `JIRA_EMAIL`: email do usuário
- `JIRA_API_TOKEN`: API token

#### OAuth 2.0 (3LO)

- `JIRA_AUTH_MODE`: `oauth2`
- `JIRA_OAUTH_ACCESS_TOKEN`: access token
- `JIRA_CLOUD_ID`: cloud id (necessário se `JIRA_BASE_URL` não for enviado)
- `JIRA_BASE_URL`: opcional, **somente** se for `https://api.atlassian.com/ex/jira/<cloud_id>` (sem `/rest/api/3`)

### Cursor

Crie/edite `~/.cursor/mcp.json` (macOS/Linux) e adicione:

```json
{
  "mcpServers": {
    "jira-mcp": {
      "url": "https://mcp.seu-dominio.com",
      "headers": {
        "JIRA_BASE_URL": "https://<site>.atlassian.net",
        "JIRA_AUTH_MODE": "oauth2",
        "JIRA_OAUTH_ACCESS_TOKEN": "<access_token>",
        "JIRA_CLOUD_ID": "<cloud_id>"
      }
    }
  }
}
```

### Codex

Edite `~/.codex/config.toml` (ou `.codex/config.toml` no projeto):

```toml
[mcp_servers.jira]
url = "https://mcp.seu-dominio.com"
headers = { JIRA_BASE_URL = "https://<site>.atlassian.net", JIRA_AUTH_MODE = "oauth2", JIRA_OAUTH_ACCESS_TOKEN = "<access_token>", JIRA_CLOUD_ID = "<cloud_id>" }
```

### Claude (Claude Code)

No projeto, Claude Code usa `.mcp.json` na raiz:

```json
{
  "mcpServers": {
    "jira-mcp": {
      "type": "http",
      "url": "https://mcp.seu-dominio.com",
      "headers": {
        "JIRA_BASE_URL": "https://<site>.atlassian.net",
        "JIRA_AUTH_MODE": "oauth2",
        "JIRA_OAUTH_ACCESS_TOKEN": "<access_token>",
        "JIRA_CLOUD_ID": "<cloud_id>"
      }
    }
  }
}
```

Para escopo de usuario, Claude Code armazena em `~/.claude.json`.

Em ambientes corporativos, `managed-mcp.json` tem o mesmo formato de `.mcp.json`. Locais do `managed-mcp.json`:
macOS: `/Library/Application Support/ClaudeCode/managed-mcp.json`
Windows: `C:\Program Files\ClaudeCode\managed-mcp.json`
Linux/WSL: `/etc/claude-code/managed-mcp.json`

### Genérico (formato estilo VS Code)

Use o formato abaixo como base (por exemplo, em `.vscode/mcp.json`) e ajuste para o seu client:

```json
{
  "servers": {
    "jira-mcp": {
      "type": "http",
      "url": "https://mcp.seu-dominio.com",
      "headers": {
        "JIRA_BASE_URL": "https://<site>.atlassian.net",
        "JIRA_AUTH_MODE": "oauth2",
        "JIRA_OAUTH_ACCESS_TOKEN": "<access_token>",
        "JIRA_CLOUD_ID": "<cloud_id>"
      }
    }
  }
}
```

## Convenção das tools

- Cada operação do OpenAPI vira uma tool `jira_<operationId>`. Se o nome exceder o limite do client (ex.: Cursor soma `server + tool` até 60), ele é encurtado e recebe um sufixo `__<hash>`.
- Os inputs incluem `path`, `query`, `header` params e, quando aplicável, `body`.
- Você pode passar headers via o campo `headers`. Autenticação deve ser enviada via `JIRA_*` (não `Authorization`).
- A resposta padrão é:

```json
{
  "status": 200,
  "headers": {"...": "..."},
  "body": {"...": "..."}
}
```

### Exemplo

```json
{
  "issueIdOrKey": "ABC-1",
  "expand": "names",
  "body": {
    "fields": {
      "summary": "Bug",
      "issuetype": {"id": "10000"},
      "project": {"id": "10001"}
    }
  }
}
```

## Resource

- `config://jira` retorna a configuração efetiva (sem segredos).
