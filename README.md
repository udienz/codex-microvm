# Codex MicroVM

A persistent OpenAI Codex CLI workspace hosted in a DigitalOcean MicroVM.

This repository contains an authenticated HTTP task API and an interactive shell workflow using DigitalOcean's supported `doctl compute microvm console` command.

## Architecture

- The MicroVM runs one `linux/amd64` container image.
- FastAPI exposes `/healthz` and `/v1/tasks` on port 8080.
- DigitalOcean endpoint requests use a token with the `microvm:access` scope. The task API adds a separate `X-API-Key` application secret.
- Tasks run `codex exec` in `/workspace` with the `workspace-write` sandbox.
- Use `doctl compute microvm console <id>` for an interactive `/bin/sh` console. The DigitalOcean console WebSocket requires an Authorization header that browser JavaScript cannot set, so this starter uses the supported CLI console.
- MicroVMs automatically pause when idle and can resume on HTTP requests, commands, or console sessions. Pausing preserves memory, files, and processes; storage billing continues.

## Security

- Never commit DigitalOcean tokens, Codex credentials, `.env` files, or workspace secrets.
- Keep `API_BEARER_TOKEN` private. Anyone with it and endpoint access can submit Codex tasks.
- The task API is intended for a trusted private client, not public internet exposure.
- Codex's `workspace-write` sandbox confines file writes to the workspace, but command execution remains powerful.
- Codex credentials are stored under `CODEX_HOME` (default `/home/codex/.codex`). Treat `auth.json` as a password.
- Never put secrets into Docker build arguments or image layers.

## Quick start

See [installation](docs/installation.md), [authentication](docs/authentication.md), and [operation](docs/operation.md).

## API

`POST /v1/tasks` requires both headers:

```http
Authorization: Bearer <DIGITALOCEAN_ENDPOINT_TOKEN>
X-API-Key: <API_BEARER_TOKEN>
Content-Type: application/json
```

Body:

```json
{"prompt":"Inspect this workspace and explain its structure."}
```

The response is an SSE stream containing Codex JSONL events and a final `done` event.

`GET /healthz` returns a minimal health status and is protected by DigitalOcean endpoint authentication.

## Scope

This is a starter scaffold, not a fully managed multi-user service. It does not implement a browser terminal, public user accounts, persistent task history, or automatic Git commits.
