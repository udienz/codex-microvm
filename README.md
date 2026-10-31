# Claude Blog Web Studio

A private, single-user browser workspace hosted in a DigitalOcean MicroVM.

## Current stage

**Stage 1 — private dashboard foundation**
- Password-protected dashboard with no public registration.
- HTTP-only, SameSite=Strict session cookie (Secure by default).
- Responsive login and dashboard UI.
- Existing authenticated API and health endpoint retained.

The skill catalog and skill execution runtime are intentionally not enabled yet.

## Architecture

- FastAPI serves the dashboard and JSON authentication endpoints on port 8080.
- DigitalOcean endpoint requests use a token with the `microvm:access` scope.
- Existing task API uses a separate `X-API-Key` application secret.
- Browser dashboard uses `STUDIO_PASSWORD_HASH` and `STUDIO_SESSION_SECRET`.
- The container runs as the non-root `codex` user.

## Setup

See [docs/studio.md](docs/studio.md), [docs/installation.md](docs/installation.md), [docs/authentication.md](docs/authentication.md), and [docs/operation.md](docs/operation.md).

Generate a password hash on a trusted machine:

```sh
python3 scripts/generate_password_hash.py
```

Generate a session signing secret:

```sh
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Add both outputs to the MicroVM environment as `STUDIO_PASSWORD_HASH` and `STUDIO_SESSION_SECRET`. Keep the existing `API_BEARER_TOKEN` as-is. Never commit real secrets.

## Existing API

`GET /healthz` remains available. `POST /v1/tasks` remains protected by the DigitalOcean endpoint token plus `X-API-Key`.

## Security

Treat all credentials as secrets. The browser session is not a replacement for DigitalOcean endpoint authentication, and the existing task API is not exposed through the dashboard in this stage.
