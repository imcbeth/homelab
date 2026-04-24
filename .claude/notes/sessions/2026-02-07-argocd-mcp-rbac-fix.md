### 2026-02-07 (Evening): ArgoCD MCP RBAC Fix

**Completed Work:**
- Diagnosed ArgoCD MCP returning empty results (JWT valid, but zero RBAC permissions)
- Added readonly RBAC policy for MCP service account in argocd-config.yaml
- Fixed stuck ArgoCD sync (argocd-redis-secret-init hook job blocking)
- Verified all 24 apps visible via MCP after fix

**Pull Requests:**
- **PR #409:** [Merged] fix: add RBAC policy for ArgoCD MCP service account

**Issues Resolved:**
1. **ArgoCD MCP empty results** - Root cause: `mcp` account had `apiKey` capability but no RBAC permissions (empty `policy.csv`). Fix: Added `configs.rbac.policy.csv` with readonly role in Helm values.
2. **ArgoCD sync stuck on hook job** - `argocd-redis-secret-init` blocking. Fix: Patched `status.operationState` to null.

**Files Modified:**
- `manifests/base/argocd/argocd-config.yaml` (RBAC policy added)
