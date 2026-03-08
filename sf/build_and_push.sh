#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <IMAGE> [DAGSTER_VERSION]"
    echo "Example: $0 myregistry/sf-dagster-webserver:1.12.18"
    echo "Example: $0 myregistry/sf-dagster-webserver:1.12.18-sf1 1.12.18"
    exit 1
fi

IMAGE="$1"
# Derive DAGSTER_VERSION from image tag if not provided (strips any suffix after the version, e.g. -sf1)
DAGSTER_VERSION="${2:-$(echo "$IMAGE" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Building $IMAGE..."
docker build \
    --platform linux/amd64 \
    --no-cache \
    -f "$REPO_ROOT/sf/Dockerfile.Auth.Webserver" \
    --build-arg DAGSTER_VERSION="$DAGSTER_VERSION" \
    -t "$IMAGE" \
    "$REPO_ROOT"

echo "Pushing $IMAGE..."
docker push "$IMAGE"

echo "Done: $IMAGE"