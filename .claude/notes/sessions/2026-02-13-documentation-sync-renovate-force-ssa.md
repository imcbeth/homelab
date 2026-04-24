### 2026-02-13: Documentation Sync, Renovate Deploy & Force/SSA Fix

**Completed Work:**
- Synced k8s-docs-n37 documentation to match live cluster state (17 files, PR #66 merged)
- Addressed Copilot review suggestions (Falco version explanation, secret count fix, Velero PVC table)
- Deployed Renovate dependency updates: kube-prometheus-stack 81.6.1 to 81.6.6, trivy-operator 0.31.0 to 0.32.0
- Diagnosed and fixed kube-prometheus-stack sync failure caused by Force=true + ServerSideApply incompatibility
- Removed stale `argocd.argoproj.io/sync: force` and `argocd.argoproj.io/sync-options: Replace=true` annotations from in-cluster Application
- Removed per-resource `Force=true` from webhook hooks in git manifest (PR #426)
- Audited all 13 SSA apps for force/replace conflicts — only kube-prometheus-stack affected
- Verified all 24 ArgoCD apps Synced and Healthy

**Pull Requests:**
- **PR #66 (k8s-docs-n37):** [Merged] docs: sync cluster state for February 2026 (17 files updated)
- **PR #426:** [Merged] fix: remove Force=true from webhook hooks incompatible with ServerSideApply

**Issues Resolved:**
1. **kube-prometheus-stack sync failure** — Stale in-cluster annotations (`argocd.argoproj.io/sync: force`, `argocd.argoproj.io/sync-options: Replace=true`) from previous manual intervention caused every sync to attempt `--force`, which is incompatible with `ServerSideApply=true`. Fix: removed stale annotations with `kubectl annotate ... -`, then normal sync succeeded.
2. **Per-resource Force=true latent risk** — PR #425 added `argocd.argoproj.io/sync-options: Force=true` on webhook hooks. While it worked in normal syncs, it's a latent risk with SSA. Fix: removed it since `HookSucceeded` delete policy already handles cleanup (PR #426).

**Key Learning:**
- `--force` is explicitly incompatible with `--server-side` in ArgoCD (hard error, not just a warning)
- `Replace=true` IS compatible with `ServerSideApply=true` (istio-base uses this pattern successfully)
- Manual `kubectl annotate` on ArgoCD Applications persists and affects ALL subsequent auto-syncs — always clean up after manual interventions

**Files Modified:**
- `manifests/applications/kube-prometheus-stack.yaml` (removed Force=true from webhook hook annotations)
- 17 files in k8s-docs-n37 (intro, hardware, overview, argocd, falco, velero, trivy-operator, secrets-management, network-policies, monitoring/overview, unipoller, external-dns, kube-prometheus-stack, loki, sidebars.ts, docusaurus.config.ts, README.md)
