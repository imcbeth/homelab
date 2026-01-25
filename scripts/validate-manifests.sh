#!/usr/bin/env bash
# Validate Kubernetes manifests using kubeconform
# This script is called by the pre-commit hook

set -e

echo "Validating Kubernetes manifests with kubeconform..."

# Find all YAML files in manifests directory (excluding secrets and non-manifests)
# Exclude:
# - secrets/* (git-crypt encrypted)
# - */values.yaml (Helm chart values, not K8s manifests)
# - *-values.yaml (Helm chart values with prefix, not K8s manifests)
# - */configs/* (ConfigMap data files)
# - *-config.yaml (Configuration files, not K8s manifests)
manifests=$(find manifests -type f \( -name "*.yaml" -o -name "*.yml" \) \
  ! -path "*/secrets/*" \
  ! -name "values.yaml" \
  ! -name "*-values.yaml" \
  ! -path "*/configs/*" \
  ! -name "*-config.yaml" \
  2>/dev/null)

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
