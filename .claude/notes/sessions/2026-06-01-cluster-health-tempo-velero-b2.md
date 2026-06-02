### 2026-06-01 (Afternoon): Cluster Health Check, Tempo Fix, Velero B2 Fix

**Completed Work:**

**Deep cluster health check (fanned-out subagents):**
- All 5 nodes Ready, all DaemonSets at expected counts, metrics API healthy
- Discovered: Tempo pod 0 ready replicas (ArgoCD Application CRD not applied + Gatekeeper blocking pod)
- Discovered: external-dns-unifi 1,598 restarts + unifi-poller 670 restarts — both currently stable; historical accumulation from periodic UniFi controller unavailability. unifi-poller has nil-pointer panic bug in v5.25.0 (`GetPortAnomaliesSite`). No immediate action needed.

**Tempo restored (PR merged inline):**
- Root cause 1: `tempo` ArgoCD Application CRD existed in repo but was never applied → namespace was empty. Fixed: `kubectl apply -f manifests/applications/tempo.yaml`
- Root cause 2: Gatekeeper `require-resource-limits` blocked pod because `resources:` in values.yaml was at top-level — chart v1.24.4 requires it under `tempo:` key
- Fix: moved `resources:`, `extraEnv:`, `podLabels:` under the `tempo:` block in `manifests/base/tempo/values.yaml`
- Result: `tempo-0 1/1 Running` ✅

**Documentation update (PRs #679, #83):**
- Updated `homelab/.claude/notes/CURRENT.md` (PR #679, merged)
- Added `k8s-docs-n37/docs/applications/argo-events.md` — EventBus/EventSource/Sensor architecture, CI pipeline, NetworkPolicy table, Cloudflare Tunnel webhook routing
- Added `k8s-docs-n37/docs/applications/lifeonabike.md` — Cloudflare Tunnel routing, CI/CD pipeline steps, in-cluster Zot HTTP push gotcha, ztunnel ambient bypass
- Updated `k8s-docs-n37/docs/applications/argo-workflows.md` — lifeonabike-build WorkflowTemplate + Artifact Storage sections
- Addressed Copilot review comment: port 80 vs 8080 discrepancy — added callout explaining ingress-nginx connects to pod endpoint (8080) while Cloudflare Tunnel uses Service (80). Components table updated.
- PR #83 merged (k8s-docs-n37, branch `docs/april-2026-updates`)

**Velero B2 backup fix (PR #680, PR #681):**
- PR #680 (merged): added `tagging: ""` to BSL config — **INEFFECTIVE**. AWS SDK sends `x-amz-tagging` header regardless of empty string value.
- PR #681 (merged): pinned `velero-plugin-for-aws` from `v1.14.1` → `v1.13.2`. v1.14.x introduced object tagging and unconditionally sends `x-amz-tagging` on every PutObject. B2 rejects it. v1.13.2 predates tagging entirely.
- Removed ineffective `tagging: ""` line from BSL config.
- Verified: `velero backup create test-b2-pin-fix --wait` → `Phase: Completed` ✅

**Makeup backups (post-fix):**
- `manual-argocd-makeup` → Completed ✅
- `manual-critical-pvcs-makeup` (CSI snapshots: default, loki, trivy-system, falco) → Completed ✅
- Deleted 3 failed/test backups: `test-b2-tagging-fix`, `velero-daily-argocd-20260601013011`, `velero-daily-critical-pvcs-20260601020011`

**Pull Requests:**
- **PR #679:** [Merged] docs: update session notes for lifeonabike CI pipeline + Argo Events
- **PR #680:** [Merged] fix(velero): attempt tagging="" BSL config for B2 — ineffective, superseded by #681
- **PR #681:** [Merged] fix: pin velero-plugin-for-aws to v1.13.2 to restore B2 backups

**Key Gotchas Discovered:**
- **tempo chart v1.24.4: `resources:` must be under `tempo:` key** — top-level is silently ignored by the chart, causing Gatekeeper `require-resource-limits` to block pod creation.
- **velero-plugin-for-aws v1.14.x incompatible with Backblaze B2**: Sends `x-amz-tagging` header on every PutObject. The `tagging: ""` BSL config does NOT suppress it. Only solution is to pin back to v1.13.x until B2 adds support or plugin adds a `disableTagging` option.
