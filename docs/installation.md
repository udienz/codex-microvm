# Installation and deployment

## Prerequisites

- A DigitalOcean account with MicroVM preview access.
- `doctl` v1.173.0 or newer.
- A DigitalOcean personal access token with the MicroVM scopes needed to create and manage MicroVMs.
- A separate endpoint token with only the `microvm:access` scope.
- A private OCI image registry if you do not publish the image publicly.

MicroVMs run `linux/amd64` container images. During the public preview, only the declared HTTP port is reachable through the MicroVM endpoint.

## Build and publish

Build for the supported architecture and push to your registry:

```sh
docker buildx build --platform linux/amd64 -f docker/Dockerfile -t REGISTRY/codex-microvm:latest --push .
```

Do not pass Codex credentials, DigitalOcean tokens, or the API bearer token as build arguments or bake them into the image.

## Create the MicroVM

Choose a region and size supported by your account. The example below uses the documented `mkc1` region and a modest 1-vCPU / 2-GiB size; verify available options and pricing before creating it.

```sh
read -rsp 'API bearer token: ' API_BEARER_TOKEN; echo
doctl compute microvm create codex-workspace \
  --oci-ref REGISTRY/codex-microvm:latest \
  --region mkc1 --cpu 1 --memory 2048 --http-port 8080 \
  --env "API_BEARER_TOKEN=$API_BEARER_TOKEN"
unset API_BEARER_TOKEN
```

Check provisioning with `doctl compute microvm get MICROVM_ID`. Record the ID and endpoint securely. Endpoint requests require a separate token with the `microvm:access` scope:

```sh
curl -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  "https://MICROVM_ID.mkc1.microvm.ondigitalocean.com/healthz"
```

The application bearer token is an additional authorization layer for task submission.

## Authenticate Codex

Open a console using `doctl compute microvm console MICROVM_ID`, then sign in:

```sh
codex login --device-auth
codex login status
```

Complete the device flow in a trusted browser. Codex credentials are stored in `CODEX_HOME` under the persistent MicroVM filesystem. Never commit or share these credentials.

## Interactive console

From a machine with authorized `doctl` credentials and an interactive terminal:

```sh
doctl compute microvm console MICROVM_ID
```

The console opens `/bin/sh` in the workload container. Type `exit` or press Ctrl+D to leave. The console WebSocket requires an Authorization header that browser JavaScript cannot set, so this starter intentionally uses the supported CLI console.
