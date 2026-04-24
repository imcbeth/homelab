### 2026-03-25: Prometheus Recovery, Renovate Batch, VPA, DR Workflow, Velero Fix

**Completed Work:**

**Prometheus Recovery:**
- Found kube-prometheus-stack Degraded (Prometheus 1/2, 127 restarts over 24 days)
- Root cause: Pod on node03, VolumeAttachment (iSCSI LUN) on node01 — Synology NAS enforces exclusive iSCSI per LUN
- Fix: `kubectl delete pod prometheus-kube-prometheus-stack-prometheus-0 -n default` → rescheduled to node01 → 2/2 Running, all 50Gi data intact

**Renovate Batch:**
- Merged: trivy-operator 0.32.1 (#509), argocd 9.4.15 (#515), kube-webhook-certgen v1.6.9 (#517), kube-prometheus-stack 82.14.1 (#518), unifi-poller v2.38.0 (#520)
- Closed superseded PR #514 (kube-prometheus-stack 82.10.5)
- Merged velero v12 chart PR #521 (later caused problems — see below)

**VPA Deployed:**
- Added `manifests/base/vpa/values.yaml`: recommender enabled, updater+admission disabled
- Added `manifests/base/vpa/vpa-objects.yaml`: 7 VPAs in updateMode:Off (Prometheus, Grafana, Loki, ArgoCD repo-server, ArgoCD app-controller, Falco, Velero)
- Created `manifests/applications/vpa.yaml`: fairwinds-stable/vpa v4.10.2, wave -4
- VPA Synced+Healthy, recommender running, showing recommendations after 2 mins (PR #522)

**Velero DR Validation Workflow:**
- Created `manifests/base/argo-workflows/backup-validation-workflow.yaml`: monthly CronWorkflow (1st of month 6am MT), 8 steps (check-bsl → verify-restore), onExit cleanup
- Created `manifests/base/argo-workflows/backup-validation-rbac.yaml`: velero-validator ServiceAccount + ClusterRole/Binding
- PR #523: Added executor.resources to argo-workflows values.yaml (Gatekeeper require-resource-limits for init/wait sidecars)
- PR #524: Added workflowtaskresults RBAC Role+RoleBinding for emissary executor (exit code 64 fix)

**Velero Binary/Chart Fix (complex root cause):**
- PR #521 (velero v12 chart) broke ALL backups: v12 CRD removed "Queued" from status.phase enum
- But root cause was actually the velero binary v1.18.0 (Renovate PR #502, merged March 13) — v1.18.0 introduced a backup-queue controller that sets "Queued" phase, but neither v11 nor v12 chart CRDs include "Queued" in the enum
- Backups have been broken since March 13 (12 days): `velero-daily-argocd-20260313013012`, `velero-daily-critical-pvcs-20260313020012`, `velero-weekly-cluster-resources-20260315030015` all stuck in "Queued" state
- PR #525: Reverted chart from v12 → v11.4.0 (necessary but not sufficient)
- PR #526: Downgraded binary from v1.18.0 → v1.17.2 (actual fix)
- Deleted stuck backups, DR validation workflow completed SUCCESSFULLY in 3m 45s — all 9/9 steps green

**Pull Requests:**
- **PRs #509, #515, #517, #518, #520, #521:** [Merged] Renovate patch updates
- **PR #522:** [Merged] feat: VPA + Velero DR validation workflow
- **PR #523:** [Merged] fix: executor resource limits (Gatekeeper)
- **PR #524:** [Merged] fix: workflowtaskresults RBAC for velero-validator executor
- **PR #525:** [Merged] fix: revert velero chart v12 → v11.4.0
- **PR #526:** [Merged] fix: downgrade velero binary v1.18.0 → v1.17.2 (restores backup functionality)

**Key Learnings:**
- Velero v1.18.0 binary introduces backup-queue controller using "Queued" phase — NOT in CRD enum (v11 or v12 chart). Pin to v1.17.2 until upstream fixes CRD. Re-upgrade cautiously.
- ArgoCD SSA CRD revert: when reverting a CRD from v12→v11, the enum constraint from v12 persists because SSA doesn't remove fields applied by a previous field manager version. Can't rely on chart downgrade alone to fix CRD schema.
- Gatekeeper require-resource-limits: Argo Workflows emissary executor injects `init` and `wait` sidecar containers. Need `executor.resources` in argo-workflows Helm values to satisfy the constraint.
- Argo Workflows emissary RBAC: `wait` container writes `workflowtaskresults.argoproj.io` — needs `create/patch` Role in the workflow namespace (separate from ClusterRole for Velero operations).
