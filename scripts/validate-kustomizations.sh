#!/usr/bin/env bash
# Validate every kustomization.yaml under manifests/ by running `kustomize build`
# and piping the result through kubeconform.
#
# Catches errors the per-file kubeconform check misses:
#   - missing resources / wrong paths
#   - patch targets that don't exist
#   - generator/transformer misconfig
#
# Behavior:
#   - If `kustomize` is not installed, prints a notice and exits 0 (so local
#     pre-commit users without kustomize are not blocked).
#   - If `kubeconform` is not installed, only `kustomize build` is run.
#   - Kustomizations that pull resources from remote git refs (slow, needs
#     network) are skipped by default. Set VALIDATE_REMOTE=1 to include them
#     (CI does this).

set -euo pipefail

if ! command -v kustomize >/dev/null 2>&1; then
  echo "kustomize not installed locally; skipping kustomization build validation"
  echo "  install: brew install kustomize"
  exit 0
fi

HAS_KUBECONFORM=0
if command -v kubeconform >/dev/null 2>&1; then
  HAS_KUBECONFORM=1
fi

VALIDATE_REMOTE="${VALIDATE_REMOTE:-0}"

failures=()
checked=0
skipped=0

while IFS= read -r kfile; do
  dir="$(dirname "$kfile")"

  if [ "$VALIDATE_REMOTE" != "1" ] && grep -qE '^\s*-\s*(https?://|github\.com/)' "$kfile"; then
    skipped=$((skipped + 1))
    echo "↷ skipping $dir (remote refs; set VALIDATE_REMOTE=1 to include)"
    continue
  fi

  checked=$((checked + 1))

  if ! out=$(kustomize build "$dir" 2>&1); then
    failures+=("$dir (kustomize build failed)")
    echo "❌ kustomize build failed for $dir"
    echo "$out" | sed 's/^/    /'
    continue
  fi

  if [ "$HAS_KUBECONFORM" -eq 1 ]; then
    if ! echo "$out" | kubeconform -summary -ignore-missing-schemas -strict >/dev/null 2>&1; then
      failures+=("$dir (kubeconform failed)")
      echo "❌ kubeconform failed for $dir"
      echo "$out" | kubeconform -summary -ignore-missing-schemas -strict 2>&1 | sed 's/^/    /' || true
    fi
  fi
done < <(find manifests -type f -name kustomization.yaml)

if [ ${#failures[@]} -gt 0 ]; then
  echo
  echo "❌ ${#failures[@]} kustomization(s) failed (of $checked checked, $skipped skipped):"
  for f in "${failures[@]}"; do
    echo "  - $f"
  done
  exit 1
fi

echo "✅ All $checked kustomization(s) build and validate successfully ($skipped skipped)"
