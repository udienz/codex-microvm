# Repository guidance

- Keep secrets out of Git, container build arguments, logs, and task output.
- Keep the HTTP API private. Require both DigitalOcean endpoint authentication and the application bearer token.
- Run Codex with the `workspace-write` sandbox; never use `--yolo` or disable sandboxing in the service.
- Treat prompts and repository contents as untrusted input. Do not add unauthenticated command execution.
- Keep the MicroVM workload on `linux/amd64` unless DigitalOcean adds another supported architecture.
- Update the docs whenever API behavior, environment variables, or deployment commands change.
