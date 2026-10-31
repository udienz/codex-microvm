# Codex MicroVM

A persistent OpenAI Codex CLI workspace hosted in a DigitalOcean MicroVM.

This repository contains a small authenticated HTTP task API and an interactive console workflow using DigitalOcean's supported `doctl compute microvm console` command.

## Architecture

- The MicroVM runs one `linux/amd64` container image.
- FastAPI exposes `/healthz` and `/v1/tasks` on the MicroVM HTTP port.
- Requests to the MicroVM endpoint are authenticated by DigitalOcean with a token that has the `microvm:access` scope. The application additionally requires its own `API_BEARER_TOKEN`.
- Tasks run `codex exec` in `/workspace` with the `workspace-write` sandbox and no interactive approval prompts.
- Use `doctl compute microvm console <id>` for an interactive `/bin/sh` console. DigitalOcean's console WebSocket requires an Authorization header that browser JavaScript cannot set, so this starter intentionally uses the supported CLI console rather than exposing a token-handling browser proxy.
- DigitalOcean automatically pauses idle MicroVMs and can resume them on a new request. Pause preserves memory, files, and running processes.

## Important security notes

- Do not commit DigitalOcean tokens, Codex credentials, `.env` files, or workspace secrets.
- Keep `API_BEARER_TOKEN` private. Anyone who has it can submit Codex tasks to this workspace.
- The task API is intended for a trusted private client, not public internet exposure.
- Codex's workspace-write sandbox confines file writes to the workspace; command execution is still powerful. Review changes and keep the MicroVM isolated.
- Codex login credentials are stored under `CODEX_HOME` (default: `/home/codex/.codex`) and persist when the MicroVM pauses. Treat `auth.json` as a password.
- Do not put secrets into Docker build arguments or image layers.

## Quick start

See [docs/installation.md](docs/installation.md), [docs/authentication.md](docs/authentication.md), and [docs/operation.md](docs/operation.md).

## API

`POST /v1/tasks`

Headers:

```http
Authorization: Bearer <API_BEARER_TOKEN>
Content-Type: application/json
```

Body:

```json
{"prompt":"Inspect this repository and explain its structure."}
```

The response is an event stream (SSE) containing Codex JSONL events and a final `done` event.

`GET /healthz` returns a minimal health status. DigitalOcean's endpoint authentication is still required for both routes.

## Current scope

This is a secure starter scaffold, not a fully managed multi-user service. It deliberately does not implement a browser terminal, public user accounts, task queue persistence, or automatic Git commits. Those can be added after the first deployment is verified.
