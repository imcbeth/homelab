#!/usr/bin/env bash
# Build and push the Flink demo image to the cluster's Zot registry.
# Must be run from this directory (manifests/base/flink-demo/docker/).
#
# Prerequisites:
#   docker buildx with ARM64 builder configured
#   docker login registry.k8s.n37.ca  (only needed for push)
#
# Usage:
#   ./build-and-push.sh [TAG]   # default TAG=1.0.0

set -euo pipefail

REGISTRY="registry.k8s.n37.ca"
IMAGE="flink-demo"
TAG="${1:-1.0.0}"
FULL_IMAGE="${REGISTRY}/${IMAGE}:${TAG}"

echo "Building ${FULL_IMAGE} for linux/arm64..."

docker buildx build \
  --platform linux/arm64 \
  --tag "${FULL_IMAGE}" \
  --push \
  .

echo ""
echo "Image pushed: ${FULL_IMAGE}"
echo ""
echo "Verify in Zot UI: https://registry.k8s.n37.ca"
echo "Or: curl https://registry.k8s.n37.ca/v2/${IMAGE}/tags/list"
