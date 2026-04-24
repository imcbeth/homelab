# 2026-04-19–21: Alert False Positives, UDR Recovery, Healthcheck Fix

## Completed Work

**Alert False Positives Resolved (PR #556):**
- `CriticalErrorLogs`: Loki ruler logged own query string → matched keyword alert. Fix: added `namespace!="loki"`
- `ExposedSecretsDetected`: Trivy flagged LocalStack moto fake AWS IDs. Fix: added `namespace!="localstack"`

**unipoller v2.39.0 Crash Loop (PR #557):**
- Root cause: nil pointer in `GetPortAnomalies` when UDR was hardware-degraded (auth failing, rate-limited after 98 restarts)
- Fix: pinned back to v2.38.0

**UDR Factory Reset + Grafana/Prometheus CrashLoopBackOff (2026-04-19~20):**
- UDR required factory reset → VLAN 1↔10 routing drop → active iSCSI sessions lost I/O → btrfs remounted Grafana (5Gi) and Prometheus (50Gi) PVCs read-only
- Fix: deleted both pods → fresh iSCSI remount → btrfs RW restored

**Cluster Healthcheck Velero `Unknown` Fix (PR #559):**
- `check-velero` queried `velero.io/schedule-name=daily-argocd` but actual label is `velero-daily-argocd` (with prefix)
- Fix: updated for-loop to `velero-daily-critical-pvcs velero-daily-argocd velero-weekly-cluster-resources`

## Key Learnings
- btrfs read-only recovery: pod delete → unmount + remount cycle clears RO state without fsck or data loss
- `VolumeAttachment ATTACHED: true` ≠ filesystem is RW — check pod logs for `read-only file system`
- Loki ruler false positive: any LogQL rule with keyword matching will match ruler's own log lines — always add `namespace!="loki"`

**PRs:** #556, #557, #559 [Merged]
