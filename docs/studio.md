# Claude Blog Web Studio setup

## Required MicroVM environment

Keep the existing `API_BEARER_TOKEN` unchanged. Add two new environment variables when updating the MicroVM:

- `STUDIO_PASSWORD_HASH`: output from `python3 scripts/generate_password_hash.py`. Generate it on a trusted local machine; do not send the plaintext password in chat or commit the hash.
- `STUDIO_SESSION_SECRET`: a separate random secret of at least 32 bytes, generated locally, for example with `python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`.

The browser session cookie is HTTP-only, SameSite=Strict, and Secure by default. Set `STUDIO_COOKIE_SECURE=false` only for local HTTP development. The application uses the existing API token as a temporary signing fallback if no session secret is supplied, but production should set a dedicated secret.

## Login

Open the MicroVM HTTPS endpoint in a browser and sign in with the studio password. There is no registration flow or username database: this is a single-user password gate. The session expires after 12 hours.

## Scope of stage 1

This release provides the private login and dashboard shell. It does not yet browse the skill repository or execute skills. Those are separate stages. The existing `/healthz` and token-protected `/v1/tasks` API remain available.

## Security notes

- Do not expose `STUDIO_PASSWORD_HASH`, `STUDIO_SESSION_SECRET`, `API_BEARER_TOKEN`, or DigitalOcean tokens in browser code or source control.
- Keep the DigitalOcean endpoint token separate from the application API token.
- The dashboard login protects the browser UI; it does not replace DigitalOcean endpoint authentication.
