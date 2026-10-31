# Authentication

There are two independent HTTP credentials:

1. **DigitalOcean endpoint token** — sent as `Authorization: Bearer ...` to the MicroVM hostname. Give this token only the `microvm:access` scope.
2. **Application API token** — set `API_BEARER_TOKEN` when creating the MicroVM. Send it to `POST /v1/tasks` in the `X-API-Key` header. Use a long random value and keep it outside source control.

Codex itself must be authenticated separately inside the MicroVM:

```sh
doctl compute microvm console MICROVM_ID
codex login --device-auth
codex login status
```

Complete the device flow in a trusted browser. Codex also supports API-key authentication; consult the current Codex CLI documentation for the supported sign-in methods. Plan entitlements and usage limits apply; do not assume every ChatGPT plan includes Codex access.

The Codex auth directory defaults to `/home/codex/.codex`. It is sensitive persistent state. Anyone who can access it may be able to use the signed-in Codex account.
