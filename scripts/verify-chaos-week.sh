#!/usr/bin/env bash
# Verify the outcome of the 3 weekly chaos-mesh Schedules.
#
# Usage: scripts/verify-chaos-week.sh
#
# Runs after Wednesday's fires (any time same day or next-day) and prints
# a per-fire verdict:
#
#   ✅ = fired, injected, recovered, no collateral
#   ⚠️  = fired but something anomalous — inspect
#   ❌ = didn't fire OR failed to recover
#   ⏭️  = not yet scheduled (only meaningful if run before Wednesday)
#
# Expected schedule (all UTC):
#   Wed 09:00 — pod-kill-prometheus
#   Wed 10:00 — network-delay-loki
#   Wed 11:00 — cpu-stress-unipoller
#
# Depends on: kubectl, jq, python3 (for date arithmetic).

set -u   # -e off: we want partial output even if kubectl fails on one check

# --- utilities ---------------------------------------------------------------

now_epoch() { date -u +%s; }

# Seconds since an ISO8601 timestamp (UTC). Empty input → very large number.
seconds_since() {
  local ts="${1:-}"
  if [ -z "$ts" ]; then
    echo "999999999"
    return
  fi
  python3 -c "
from datetime import datetime, timezone
ts = '$ts'.replace('Z', '+00:00')
diff = (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds()
print(int(diff))
"
}

# Format seconds as human-readable "Nh Mm ago" / "Nd ago"
humanize_ago() {
  local s="$1"
  python3 -c "
s = int('$s')
if s < 60: print(f'{s}s ago')
elif s < 3600: print(f'{s//60}m ago')
elif s < 86400: print(f'{s//3600}h {(s%3600)//60}m ago')
else: print(f'{s//86400}d {(s%86400)//3600}h ago')
"
}

# --- global cluster health ---------------------------------------------------

echo "=========================================================================="
echo "                  Chaos-Mesh Weekly Fire Verification"
echo "                  $(date -u +%FT%TZ) (now)"
echo "=========================================================================="
echo ""
echo "--- Global cluster health ---"

# All ArgoCD apps Synced+Healthy?
off=$(kubectl get application -n argocd --no-headers 2>/dev/null \
  | awk '$2 != "Synced" || $3 != "Healthy"' | wc -l | tr -d ' ')
if [ "$off" = "0" ]; then
  echo "  ✅ ArgoCD apps: all Synced+Healthy"
else
  echo "  ⚠️  ArgoCD apps: $off off-status"
  kubectl get application -n argocd --no-headers 2>/dev/null \
    | awk '$2 != "Synced" || $3 != "Healthy" {print "     "$0}'
fi

# Any chaos-mesh pods pause-swapped (image contains "pause")?
paused=$(kubectl get pod -n chaos-mesh -o json 2>/dev/null \
  | jq -r '.items[] | select(.spec.containers[0].image | contains("pause")) | .metadata.name')
if [ -z "$paused" ]; then
  echo "  ✅ chaos-mesh: no pods paused"
else
  echo "  ❌ chaos-mesh: $(echo "$paused" | wc -l | tr -d ' ') pods still paused after their duration (self-lockup?):"
  echo "$paused" | sed 's/^/     /'
fi

# Any pending/firing ArgoCDApp* alerts?
prom_pod=$(kubectl -n default get pod -l app.kubernetes.io/name=prometheus \
  -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$prom_pod" ]; then
  alert_state=$(kubectl -n default exec "$prom_pod" -c prometheus -- \
    wget -qO- 'http://localhost:9090/api/v1/query?query=ALERTS{alertname=~"ArgoCDApp.*",alertstate=~"pending|firing"}' 2>/dev/null \
    | jq -r '.data.result | length')
  if [ "${alert_state:-0}" = "0" ]; then
    echo "  ✅ ArgoCDApp* alerts: all inactive"
  else
    echo "  ⚠️  ArgoCDApp* alerts: $alert_state pending/firing"
  fi
else
  echo "  ⚠️  Prometheus pod not reachable — can't check alert state"
fi

# Any RO mounts detected?
if [ -n "$prom_pod" ]; then
  ro=$(kubectl -n default exec "$prom_pod" -c prometheus -- \
    wget -qO- 'http://localhost:9090/api/v1/query?query=count(pvc_mount_readonly==1)' 2>/dev/null \
    | jq -r '.data.result[0].value[1] // "0"')
  if [ "${ro:-0}" = "0" ]; then
    echo "  ✅ PVC RO mounts: 0"
  else
    echo "  ⚠️  PVC RO mounts: $ro (remediator should recover within 4 min)"
  fi
fi

# --- per-schedule verification ----------------------------------------------

verify_schedule() {
  local sched="$1"
  local expected_kind="$2"   # PodChaos | NetworkChaos | StressChaos
  local hint="$3"
  local action="${4:-}"      # optional: "pod-kill" → no recovery expected
  local now
  now=$(now_epoch)

  echo ""
  echo "--- Schedule: $sched ($hint) ---"

  # Schedule exists?
  if ! kubectl get schedule.chaos-mesh.org -n chaos-mesh "$sched" >/dev/null 2>&1; then
    echo "  ❌ Schedule missing from cluster"
    return
  fi

  # Find the most recent child experiment. `Schedule.status.lastScheduleTime`
  # is NEVER populated by chaos-mesh in our cluster (verified 2026-07-15 —
  # 3 fires that day all showed lastScheduleTime="" even though experiments
  # ran). Key off child experiment creationTimestamp instead.
  local child_json_all
  child_json_all=$(kubectl get "${expected_kind}.chaos-mesh.org" -n chaos-mesh -o json 2>/dev/null)

  local child_name
  child_name=$(echo "$child_json_all" | jq -r --arg s "$sched" '
    [.items[]
     | select(.metadata.ownerReferences[]?.name == $s)
     | {name: .metadata.name, created: .metadata.creationTimestamp}]
    | sort_by(.created) | last | .name // empty
  ')
  if [ -z "$child_name" ]; then
    # Owner-reference may have been cleaned up already; search by name prefix
    child_name=$(echo "$child_json_all" | jq -r --arg s "$sched" '
      [.items[]
       | select(.metadata.name | startswith($s))
       | {name: .metadata.name, created: .metadata.creationTimestamp}]
      | sort_by(.created) | last | .name // empty
    ')
  fi
  if [ -z "$child_name" ]; then
    echo "  ⏭️  No child ${expected_kind} found — this Schedule has never fired (or historyLimit pruned all runs)"
    return
  fi

  local child_created
  child_created=$(echo "$child_json_all" | jq -r --arg n "$child_name" '
    .items[] | select(.metadata.name == $n) | .metadata.creationTimestamp
  ')
  local since
  since=$(seconds_since "$child_created")
  echo "  latest child: $child_name ($(humanize_ago "$since"))"

  # If most recent fire was > 8 days ago, this week's slot didn't fire
  if [ "$since" -gt 691200 ]; then
    echo "  ❌ Last fire was > 8 days ago — this week's slot may not have fired"
    return
  fi

  # Inspect its conditions + records
  local child_json
  child_json=$(kubectl get "${expected_kind}.chaos-mesh.org" -n chaos-mesh "$child_name" -o json 2>/dev/null)

  # NOTE (2026-07-22): chaos-mesh resets AllInjected/AllRecovered to False
  # after the experiment completes (records transition to phase="Not Injected"
  # once recovered). The truth of "did it work?" is in the record-level
  # `injectedCount` and `recoveredCount`, plus the record's event history.
  # v1 of this script keyed off the parent conditions and misreported clean
  # runs as ❌ Failed to inject. Now we count records + look at their events.
  local n_records n_injected n_recovered n_failed_events n_success_events
  n_records=$(echo "$child_json" | jq -r '.status.experiment.containerRecords | length // 0')
  n_injected=$(echo "$child_json" | jq -r '[.status.experiment.containerRecords[]? | select((.injectedCount // 0) >= 1)] | length')
  n_recovered=$(echo "$child_json" | jq -r '[.status.experiment.containerRecords[]? | select((.recoveredCount // 0) >= 1)] | length')
  n_failed_events=$(echo "$child_json" | jq -r '[.status.experiment.containerRecords[]?.events[]? | select(.type=="Failed")] | length')
  n_success_events=$(echo "$child_json" | jq -r '[.status.experiment.containerRecords[]?.events[]? | select(.type=="Succeeded")] | length')

  # Verdict logic. pod-kill has no "recovery" phase (the pod is dead and
  # recreated fresh by the workload controller) — chaos-mesh will show
  # recoveredCount stuck at 0. Skip the recovered check in that case.
  if [ "$action" = "pod-kill" ]; then
    if [ "$n_injected" -ge 1 ] && [ "$n_failed_events" = "0" ]; then
      echo "  ✅ Pod killed successfully ($n_injected/$n_records records injected; pod-kill has no recovery phase)"
    elif [ "$n_injected" -ge 1 ]; then
      echo "  ⚠️  Killed but ${n_failed_events} failure event(s):"
      echo "$child_json" | jq -r '.status.experiment.containerRecords[]?.events[]?
        | select(.type=="Failed") | "     - "+.message' | head -3
    else
      echo "  ❌ pod-kill failed to inject (chaos-daemon reachable? selector matches?)"
    fi
    return
  fi

  if [ "$n_injected" -ge 1 ] && [ "$n_recovered" -ge 1 ] && [ "$n_failed_events" = "0" ]; then
    echo "  ✅ Injected + Recovered cleanly ($n_injected/$n_records injected, $n_recovered recovered, $n_success_events success events)"
  elif [ "$n_injected" -ge 1 ] && [ "$n_recovered" -ge 1 ]; then
    echo "  ⚠️  Injected + Recovered ($n_injected/$n_records) but ${n_failed_events} failure event(s) during injection:"
    echo "$child_json" | jq -r '.status.experiment.containerRecords[]?.events[]?
      | select(.type=="Failed") | "     - "+.message' | head -3
  elif [ "$n_injected" -ge 1 ] && [ "$n_recovered" = "0" ]; then
    echo "  ❌ Injected ($n_injected/$n_records) but NOT recovered — investigate"
  elif [ "$n_injected" = "0" ]; then
    echo "  ❌ Failed to inject — chaos-daemon reachable? selector matches? ($n_records records, $n_failed_events fail events)"
    echo "$child_json" | jq -r '.status.experiment.containerRecords[]?.events[]?
      | select(.type=="Failed") | "     - "+.message' | head -3
  else
    echo "  ⚠️  Ambiguous state: injected=$n_injected/$n_records recovered=$n_recovered failed_events=$n_failed_events"
  fi
}

verify_schedule "pod-kill-prometheus" "PodChaos" \
  "Wed 09:00 UTC — kills 1 Prometheus pod, expect StatefulSet recovery" \
  "pod-kill"

# Prometheus-specific extras
prom_age_min=$(kubectl get pod -n default prometheus-kube-prometheus-stack-prometheus-0 \
  -o jsonpath='{.status.startTime}' 2>/dev/null | while read t; do seconds_since "$t"; done)
if [ -n "${prom_age_min:-}" ]; then
  if [ "$prom_age_min" -lt 86400 ]; then
    echo "  → prometheus-0 age: $(humanize_ago "$prom_age_min") (fresh restart consistent with a fire this week)"
  else
    echo "  → prometheus-0 age: $(humanize_ago "$prom_age_min") (no recent kill — check if fire missed)"
  fi
fi

verify_schedule "network-delay-loki" "NetworkChaos" \
  "Wed 10:00 UTC — adds 200ms delay to Loki traffic, expect ip-set apply to succeed"

verify_schedule "cpu-stress-unipoller" "StressChaos" \
  "Wed 11:00 UTC — 3m CPU stress on unipoller, expect Gatekeeper CPU limit to hold"

echo ""
echo "=========================================================================="
echo "Interpretation guide:"
echo "  ✅ All 3 schedules ✅ + global health ✅ = normal week, no action needed"
echo "  ⚠️  on any = read the finding, may need investigation or may be benign"
echo "  ❌ on any = something to fix before next Wednesday"
echo "=========================================================================="
