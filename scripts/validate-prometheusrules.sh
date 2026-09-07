#!/usr/bin/env bash
# Assert every PrometheusRule under manifests/ carries the label that makes
# Prometheus actually load it.
#
# WHY THIS EXISTS
#
# Prometheus's ruleSelector is `matchLabels: {release: kube-prometheus-stack}`.
# A PrometheusRule without that label is created successfully, shows up in
# `kubectl get prometheusrule`, reports no error anywhere — and is NEVER
# loaded. Its alerts simply do not exist.
#
# This has bitten the cluster three times:
#   2026-07-31  velero-alerts dormant 198 days (PR #848). The alerts that
#               would have caught 16 days of silent backup failure.
#   2026-09-07  six more found at once (PR #896): blackbox-exporter,
#               log-pipeline, network, pi-cluster, slo, storage. Undervoltage
#               detection and the whole SLO burn-rate framework had never
#               evaluated. Rule groups went 55 -> 70 once fixed.
#
# A note in REFERENCE.md was already there before the second occurrence, so
# documentation alone demonstrably does not prevent this. Hence a hard check.
#
# Exits non-zero listing every offending file.

set -uo pipefail

REQUIRED_LABEL_KEY="release"
REQUIRED_LABEL_VALUE="kube-prometheus-stack"

echo "Checking PrometheusRule label (${REQUIRED_LABEL_KEY}: ${REQUIRED_LABEL_VALUE})..."

# Prefer files passed by pre-commit; otherwise scan all of manifests/.
if [ "$#" -gt 0 ]; then
  candidates=("$@")
else
  mapfile -t candidates < <(find manifests -type f \( -name '*.yaml' -o -name '*.yml' \) 2>/dev/null)
fi

missing=()
checked=0

for f in "${candidates[@]}"; do
  [ -f "$f" ] || continue
  # Cheap pre-filter so we only parse files that could matter.
  grep -q 'kind:[[:space:]]*PrometheusRule' "$f" 2>/dev/null || continue

  # A single file may hold several documents; check each PrometheusRule.
  result=$(python3 - "$f" <<'PY'
import sys, yaml

path = sys.argv[1]
try:
    with open(path) as fh:
        docs = list(yaml.safe_load_all(fh))
except Exception as exc:                      # malformed YAML is the YAML
    print(f"PARSE_ERROR {exc}")               # linter's job, not ours
    sys.exit(0)

bad, total = [], 0
for doc in docs:
    if not isinstance(doc, dict) or doc.get("kind") != "PrometheusRule":
        continue
    total += 1
    labels = (doc.get("metadata") or {}).get("labels") or {}
    if labels.get("release") != "kube-prometheus-stack":
        name = (doc.get("metadata") or {}).get("name", "<unnamed>")
        bad.append(f"{name} (labels: {sorted(labels) or 'none'})")

print(f"TOTAL {total}")
for b in bad:
    print(f"BAD {b}")
PY
)

  # Skip files we could not parse — yamllint owns that failure.
  if grep -q '^PARSE_ERROR' <<<"$result"; then
    continue
  fi

  n=$(grep '^TOTAL ' <<<"$result" | awk '{print $2}')
  checked=$(( checked + ${n:-0} ))

  while IFS= read -r line; do
    [ -n "$line" ] && missing+=("$f → ${line#BAD }")
  done < <(grep '^BAD ' <<<"$result" || true)
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo ""
  echo "❌ ${#missing[@]} PrometheusRule(s) missing '${REQUIRED_LABEL_KEY}: ${REQUIRED_LABEL_VALUE}':"
  for m in "${missing[@]}"; do
    echo "     $m"
  done
  cat <<'EOF'

Without that label Prometheus's ruleSelector never matches the rule. It will
be created without error and silently never load — every alert inside it is
inert. Add to metadata.labels:

    release: kube-prometheus-stack

Then confirm it actually loaded (creation alone proves nothing):

    kubectl -n default exec prometheus-kube-prometheus-stack-prometheus-0 \
      -c prometheus -- wget -qO- localhost:9090/api/v1/rules \
      | grep -c '<YourAlertName>'
EOF
  exit 1
fi

echo "✅ All ${checked} PrometheusRule(s) carry the required label"
