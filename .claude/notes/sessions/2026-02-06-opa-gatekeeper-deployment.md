# 2026-02-06: OPA Gatekeeper Deployment

**Completed Work:**
- Deployed OPA Gatekeeper v3.21.1 for Kubernetes admission control
- Created 5 ConstraintTemplates (Rego): resource limits, allowed repos, required labels, block NodePort, container limits
- Created 5 Constraints in dryrun mode for audit-first rollout
- Split into 2 ArgoCD Applications (gatekeeper + gatekeeper-policies) to handle CRD ordering
- Created NetworkPolicy for gatekeeper-system namespace
- Created k8s-docs-n37 application guide and updated runtime-security docs
- Updated sidebar navigation in k8s-docs-n37

**Pull Requests:**
- **PR #389:** [Merged] feat: deploy OPA Gatekeeper for admission control
- **PR #390:** [Merged] fix: remove duplicate source path from gatekeeper Application
- **PR #391:** [Merged] fix: add sync waves for gatekeeper CRD ordering
- **PR #392:** [Merged] fix: split gatekeeper constraints into separate ArgoCD Application

**Issues Resolved:**

1. **Duplicate resources in ArgoCD multi-source app**
   - Root cause: Source 2 had both `path` and `ref`, causing it to render manifests AND serve as a values ref
   - Fix: Removed `path` from the ref source

2. **ConstraintTemplate/Constraint CRD ordering**
   - Root cause: ArgoCD validates ALL resources before syncing ANY; constraint CRDs only exist after Gatekeeper processes ConstraintTemplates
   - Fix: Split into two Applications - gatekeeper (wave -6) for Helm+Templates, gatekeeper-policies (wave -5) for Constraints with generous retries

**Audit Results (dryrun):**
- 156 resource-limit violations
- 20 allowed-repo violations
- 15 require-label violations
- 0 block-nodeport violations
- 0 container-limit violations

**Files Created/Modified:**
- `manifests/applications/gatekeeper.yaml` (new)
- `manifests/applications/gatekeeper-policies.yaml` (new)
- `manifests/base/gatekeeper/` (new directory - values, kustomization, constraint-templates, constraints)
- `manifests/base/network-policies/gatekeeper-system/network-policy.yaml` (new)
- `manifests/base/network-policies/kustomization.yaml` (added gatekeeper-system)
- `TODO.md` (marked OPA Gatekeeper items done)
