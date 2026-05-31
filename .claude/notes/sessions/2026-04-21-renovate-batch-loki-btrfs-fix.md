# 2026-04-21 (Evening): Renovate Batch, Loki btrfs Fix, Rollout Monitoring

## Completed Work

### Renovate Dashboard Review

- Identified 2 open PRs + 2 awaiting-schedule patches
- PR #558 (unipoller v2.39.0): Previously pinned due to crash bug. Re-reviewed — API key (`api-key`) was already in `unipoller-secret` and wired via `UP_UNIFI_CONTROLLER_0_API_KEY`. The crash was caused by the UDR being hardware-degraded during the outage, not a missing key. Safe to merge with healthy UDR.
- PR #554 (external-dns image v0.20.0→v0.21.0): Clean image-tag-only diff, no conflict with lifeonabike.ca args added in #553.
- Triggered awaiting-schedule PRs #560 (argo-cd 9.5.3) and #561 (kube-prometheus-stack 83.7.0) via Renovate dashboard checkbox edit.

### All 4 PRs merged and deployed

- **PR #554:** external-dns image v0.20.0→v0.21.0 — both cloudflare + unifi pods rolled, 0 restarts ✅
- **PR #558:** unipoller v2.38.0→v2.39.0 — clean startup, `Save Anomalies true`, exporting 1783 metrics/20s, 0 errors ✅
- **PR #560:** argo-cd chart 9.5.2→9.5.3 — Synced+Healthy ✅
- **PR #561:** kube-prometheus-stack 83.6.0→83.7.0 — 175 PreSync hooks completed, Synced+Healthy ✅

### loki-0 btrfs CrashLoopBackOff (280 restarts) — discovered during rollout monitoring

- Same root cause as Grafana/Prometheus (UDR factory reset, 2026-04-19): btrfs remounted PVC read-only.
- Error: `unlinkat /var/loki/tsdb-shipper-active/scratch: read-only file system`
- Fix: `kubectl delete pod loki-0 -n loki` → fresh remount → 2/2 Running, 0 restarts ✅
- All 3 UDR-affected PVCs now confirmed RW: Grafana (5Gi/node02), Prometheus (50Gi/node01), Loki (20Gi/node03)

### Application manifests applied manually (required pattern)

- `kubectl apply` on `manifests/applications/argocd.yaml` and `manifests/applications/kube-prometheus-stack.yaml` after PR merges — ArgoCD self-management does NOT auto-deploy Application spec changes.

## Pull Requests

- **PR #554:** [Merged] chore: external-dns image v0.21.0
- **PR #558:** [Merged] chore: unipoller v2.39.0
- **PR #560:** [Merged] chore: argo-cd chart 9.5.3
- **PR #561:** [Merged] chore: kube-prometheus-stack 83.7.0

## Key Learnings

- unipoller v2.39.0 crash was UDR-induced, not a config issue. API key was already in place. Re-upgrade safe once UDR is healthy.
- Loki btrfs read-only from same UDR event — wasn't caught in initial PVC audit because `loki-0` showed 0 restarts at that time (280 restarts accumulated over 2 days). Always check ArgoCD app health status, not just pod restarts.
- `kube-prometheus-stack` auto-sync picks up the Helm chart version change after `kubectl apply` on the Application manifest — no manual `argocd app sync` needed once the Application is updated.
