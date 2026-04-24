# 2026-03-01 (Afternoon): Migrate Promtail to Grafana Alloy

**Completed Work:**
- Migrated log collector from Promtail (EOL March 2, 2026) to Grafana Alloy v1.13.0
- Alloy Helm chart 1.6.0 deployed as DaemonSet (5 pods, one per node)
- Uses `loki.source.kubernetes` for K8s API-based log tailing (no hostPID needed)
- Preserved selective labelmap regex to stay under Loki's 15 label limit
- Updated NetworkPolicy port 3101 → 12345 (Alloy metrics)
- Updated Grafana dashboard (loki-stack-monitoring) with Alloy references
- Updated Renovate grouping from promtail → alloy
- Cleaned up orphaned Promtail resources (DaemonSet, Service, ServiceAccount, ServiceMonitor, ClusterRole, ClusterRoleBinding)
- 288K+ log entries successfully sent to Loki from control-plane node alone
- All 25 ArgoCD apps accounted for (alloy replaced promtail)

**Pull Requests:**
- **PR #488:** [Merged] feat: migrate log collector from Promtail to Grafana Alloy

**Issues Resolved:**
1. **Promtail EOL** — Replaced with Alloy before March 2 deadline. Same log pipeline, modern collector.
2. **Orphaned resources** — Deleting ArgoCD app before it could prune left Promtail resources. Manually cleaned up DaemonSet + 5 ancillary resources.
3. **Initial catchup errors** — Alloy tries to replay old terminated container logs that exceed Loki's ingestion window ("entry too far behind"). Expected behavior, self-resolves.

**Key Learning:**
- When replacing an ArgoCD app (changing app name), delete the old app first, then create new one. Old resources become orphaned and need manual cleanup.
- Alloy's `loki.source.kubernetes` component uses K8s API to tail logs — simpler than Promtail's file-based approach, no /var/log mounts or hostPID needed.
- Alloy has a config-reloader sidecar by default (2 containers per pod vs Promtail's 1).
- Alloy metrics port is 12345 (vs Promtail's 3101) — NetworkPolicy must be updated.

**Files Created:**
- `manifests/applications/alloy.yaml`
- `manifests/base/alloy/values.yaml`

**Files Deleted:**
- `manifests/applications/promtail.yaml`
- `manifests/base/promtail/values.yaml`

**Files Modified:**
- `manifests/base/network-policies/loki/network-policy.yaml` (port 3101 → 12345)
- `manifests/base/grafana/dashboards/loki-stack-monitoring.yaml` (Promtail → Alloy)
- `manifests/base/loki/values.yaml` (comment update)
- `renovate.json` (promtail → alloy)
