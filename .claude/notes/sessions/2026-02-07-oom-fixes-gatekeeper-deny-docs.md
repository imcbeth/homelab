### 2026-02-07: OOM Fixes, Gatekeeper Deny Mode & Docs Sync

**Completed Work:**
- Fixed 12 Gatekeeper resource-limit violations across multiple apps
- Switched OPA Gatekeeper from dryrun to deny mode (0 violations)
- Fixed OOMKilled containers: Grafana sidecars (256Mi), Loki sidecar/canary, Falco redis-stack
- Configured Falco redis-stack maxmemory (700Mi)
- Synced k8s-docs-n37 documentation (10 files updated)
- Cleaned up stale PVs

**Pull Requests:**
- **PR #405:** [Merged] fix: increase Grafana sidecar and Loki memory limits for OOMKill prevention
- **PR #407:** [Merged] fix: limit Falco redis to 700mb maxmemory
- **PR #408:** [Merged] fix: add missing resource limits for Gatekeeper violations
- **PR #64 (k8s-docs-n37):** [Merged] docs: sync cluster state for February 2026

**Issues Resolved:**
1. **Grafana sidecar OOMKill** - k8s-sidecar watching ConfigMaps across many namespaces needs 256Mi+
2. **Falco redis-stack memory** - Modules (RediSearch, TimeSeries, JSON, Bloom, Gears) consume significant memory; needs `maxmemory` config
3. **Loki canary value path** - `monitoring.selfMonitoring.lokiCanary.resources` is ignored; use top-level `lokiCanary.resources`

**Files Modified:**
- `manifests/base/kube-prometheus-stack/values.yaml` (sidecar resources)
- `manifests/base/loki/values.yaml` (sidecar + canary resources)
- `manifests/base/falco/values.yaml` (redis maxmemory)
- `manifests/base/gatekeeper/constraints/` (dryrun → deny)
- Multiple k8s-docs-n37 files (10 files, 142 insertions)
