# Operating the workspace

## Submit a task

Both authorization layers are required:
- DigitalOcean endpoint authentication uses `Authorization: Bearer $DIGITALOCEAN_TOKEN`.
- The application token uses `X-API-Key: $API_BEARER_TOKEN`.

```sh
curl --no-buffer \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  -H "X-API-Key: $API_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Inspect this workspace and summarize its contents."}' \
  "https://MICROVM_ID.mkc1.microvm.ondigitalocean.com/v1/tasks"
```

The response is Server-Sent Events. Each `codex` event contains one JSONL line from `codex exec --json`, followed by a `done` event with the exit code.

## Interactive shell

```sh
doctl compute microvm console MICROVM_ID
```

Inside the console, work in `/workspace`. Codex credentials persist under `/home/codex/.codex`.

## Pause and resume

MicroVMs automatically pause after their idle timeout and resume on an HTTP request, command, or console session when auto-resume is enabled. Pausing preserves memory, files, and running processes. Compute billing stops while paused, but storage billing continues.

```sh
doctl compute microvm pause MICROVM_ID
doctl compute microvm resume MICROVM_ID
```

## Important limitations

- The API streams task output directly; it does not provide a durable task queue or history.
- The starter has a per-task timeout but no persistent job scheduler or multi-user queue. Keep it private and restrict who can submit tasks.
- A browser terminal is not included. DigitalOcean's console WebSocket requires an Authorization header that browsers cannot set.
- Do not expose the MicroVM endpoint or application token publicly without an additional access-control layer.
