# Authentication

There are two independent credentials:

1. **DigitalOcean endpoint token** — send as `Authorization: Bearer ...` to the MicroVM hostname. Give this token only the `microvm:access` scope.
2. **Application API token** — set `API_BEARER_TOKEN` when creating the MicroVM. Send it to `POST /v1/tasks` as a Bearer token. Use a long random value and keep it outside source control.

Codex itself must be authenticated separately inside the MicroVM:

```sh
doctl compute microvm console MICROVM_ID
codex login --device-auth
codex login status
```

Use the ChatGPT sign-in option if available for the account and plan, or configure an API key according to the current Codex CLI documentation. Plan entitlements and usage limits apply. Do not assume that a ChatGPT Free account includes Codex access.

The Codex auth directory defaults to `/home/codex/.codex`. It is sensitive persistent state. Anyone who can access it may be able to use the signed-in Codex account.
