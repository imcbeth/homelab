### 2026-03-12 (Evening): TODO Cleanup, Renovate Batch, Monitoring Stack Upgrade

**Completed Work:**
- Reviewed and fixed TODO.md formatting/sequencing across all 24 sections (PR #504, merged)
- Synced k8s-docs-n37 todo.md to mirror homelab (full rewrite, PR #74, merged)
- Addressed Copilot review suggestions on both PRs (inline comments)
- Reviewed Renovate Dependency Dashboard (issue #251): triggered 4 safe patch PRs (#505-508)
- Merged and applied Renovate patch updates: alloy 1.6.1→1.6.2, argo-workflows 0.47.3→0.47.5, argocd 9.4.9→9.4.10, sealed-secrets 2.18.3→2.18.4
- Merged and applied PR #500 (kube-prometheus-stack 82.4.3→82.10.3, loki 6.53.0→6.55.0)
- Resolved kube-prometheus-stack stuck sync (HookSucceeded race condition on PreSync job — cleared operationState + operation)
- All 25 apps validated: Synced + Healthy

**Pull Requests:**
- **PR #504:** [Merged] docs: fix TODO.md formatting and sequencing across all 24 sections
- **PR #74 (k8s-docs-n37):** [Merged] docs: sync todo.md with homelab source of truth
- **PRs #505-508:** [Merged] Renovate: alloy, argo-workflows, argocd, sealed-secrets patches
- **PR #500:** [Merged] chore: upgrade kube-prometheus-stack 82.10.3 + loki 6.55.0

**Issues Resolved:**
1. **Copilot inline comments missed** — `gh pr view --json reviews` doesn't show inline comments. Must use `gh api repos/.../pulls/N/comments` for inline review comments.
2. **k8s-docs-n37 MDX build failure** — Bare URL auto-converted to `<https://...>` which MDX parses as JSX. Fixed to `[text](url)` format.
3. **kube-prometheus-stack stuck PreSync** — HookSucceeded race: job completed+deleted before ArgoCD informer caught it. Cleared `/status/operationState` and `/operation`, then synced.
4. **Renovate trigger** — Edited issue #251 body via `gh issue edit` to check patch checkboxes, triggering PR creation.

**Deferred (user aware):**
- argo-workflows v1 (major — high risk, deferred)
- cert-manager v1.20.0 (minor)
- gatekeeper v3.22.0 (minor)
- ingress-nginx v4.15.0 (minor)
