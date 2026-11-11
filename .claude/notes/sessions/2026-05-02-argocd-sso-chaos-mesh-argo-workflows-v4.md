# 2026-05-02/03: ArgoCD SSO Fix, chaos-mesh Recovery, Argo Workflows v4, oauth2-proxy Login Fix

## Completed Work

### ArgoCD GitHub SSO — users saw no apps after login (PR #609, merged)
- Root cause: default `scopes: '[groups]'` + empty GitHub `groups` claim = `g, imcbeth, role:admin` never fired
- Fix: added `scopes: '[preferred_username]'` to `manifests/base/argocd/argocd-config.yaml`

### chaos-mesh — all pods on node04 crashing (node04 image corruption)
- Root cause: containerd content store corruption on node04; chaos-mesh images resolved to `pause:latest`
- Fix: tainted node04 → deleted Deployment pods → `crictl rmi` all chaos-mesh images via debug pod → untainted → fresh pull

### Argo Workflows v4 CronWorkflow fix (PR #610, merged)
- Root cause: v4.0 renamed `schedule:` (string) → `schedules:` (array); both CronWorkflows used old format → silently never fired
- Fix: updated both `cluster-healthcheck-workflow.yaml` and `backup-validation-workflow.yaml`
- Also fixed: removed `path:` from ref-only source in `manifests/applications/argo-workflows.yaml` to stop duplicate resource warnings

### oauth2-proxy login redirect — all 3 protected ingresses returned blank 401 (PR #611, merged)
- Root cause: `$escaped_request_uri` not in ingress-nginx v1.14.3 nginx variable allowlist → auth-signin annotation silently rejected → no `error_page 401` redirect generated in nginx.conf
- Fix: changed `$scheme%3A%2F%2F$host$escaped_request_uri` → `$scheme://$host$uri` in all 3 ingresses
- Used `$uri` (not `$request_uri`) to avoid `&` in query strings breaking the `rd=` parameter
- Affected: `argo-workflows/argo-workflows-ingress`, `falco/falco-ui-ingress`, `uptime-kuma/values.yaml`

## Key Gotchas
- ingress-nginx v1.14.x has a strict nginx variable allowlist for `auth-signin`; `$escaped_request_uri` is NOT on it → annotation silently rejected, no redirect generated
- Use `$scheme://$host$uri` (not `$request_uri`) in `auth-signin` `rd=` param to avoid `&` in query strings breaking redirect

## Pull Requests
- **PR #609:** [Merged] fix: set argocd rbac scopes to preferred_username for GitHub SSO
- **PR #610:** [Merged] fix: update CronWorkflows to v4 schedules array, fix duplicate resources
- **PR #611:** [Merged] fix: replace $escaped_request_uri with $uri in oauth2-proxy auth-signin
