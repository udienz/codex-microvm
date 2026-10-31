#!/bin/sh
set -eu

: "${IMAGE_REF:?Set IMAGE_REF to your registry/image:tag}"
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

docker buildx build \
  --platform linux/amd64 \
  --file "$ROOT/docker/Dockerfile" \
  --tag "$IMAGE_REF" \
  --push \
  "$ROOT"
