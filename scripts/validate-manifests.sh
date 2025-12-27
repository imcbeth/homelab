#!/usr/bin/env bash
# Validate Kubernetes manifests using kubeconform
# This script is called by the pre-commit hook

set -e

echo "Validating Kubernetes manifests with kubeconform..."

# Find all YAML files in manifests directory (excluding secrets)
manifests=$(find manifests -type f \( -name "*.yaml" -o -name "*.yml" \) ! -path "*/secrets/*" 2>/dev/null)

if [ -z "$manifests" ]; then
  echo "No manifests found to validate"
  exit 0
fi

# Validate manifests
# -ignore-missing-schemas: Don't fail on CRDs or resources without schemas
# -summary: Show summary of results
# -output json: Machine-readable output for debugging
echo "$manifests" | xargs kubeconform \
  -summary \
  -output json \
  -ignore-missing-schemas

exit_code=$?

if [ $exit_code -eq 0 ]; then
  echo "✅ All Kubernetes manifests are valid"
else
  echo "❌ Some manifests failed validation"
fi

exit $exit_code
