# Homelab Repository — Claude Instructions

## What This Repo Is

GitOps-managed Kubernetes homelab on 5x Raspberry Pi 5 (16GB each, ARM64). All cluster state is declared here and reconciled by ArgoCD.

## Repository Structure

```
manifests/
  applications/   # ArgoCD Application CRDs (one per app)
  base/<app>/     # Helm values, Kustomize overlays, custom resources
.claude/
  notes/
    CURRENT.md    # Last 3-5 sessions + current cluster state — READ THIS FIRST
    REFERENCE.md  # Stable gotchas, patterns, architecture
    sessions/     # Archived session history
  skills/         # Invokable skills (see below)
TODO.md           # Active roadmap and priorities
```

## Start of Session

Always read `.claude/notes/CURRENT.md` before doing anything else. It contains:
- Current cluster state (what's deployed, what's broken)
- Last 3-5 sessions with context
- Pending next steps

Use the `/catch-up` skill for a guided summary.

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/catch-up` | Summarise recent sessions and current state |
| `/renovate-apply` | Step-by-step process for applying Renovate batch PRs |
| `/cluster-shutdown` | Safe cluster shutdown procedure |
| `/cluster-healthcheck` | Validate cluster health post-startup or post-change |

## Key Rules

### PR Workflow (Mandatory)
Direct pushes to `main` are blocked. Always:
1. Create a feature branch
2. Make changes
3. Open PR → merge
4. ArgoCD auto-syncs within ~3 minutes

### Application Manifests Require Manual Apply
Files in `manifests/applications/` are **NOT** auto-deployed by ArgoCD self-management.
After merging changes to an Application spec, always run:
```bash
kubectl apply -f manifests/applications/<app>.yaml
```

### MCP Tools First
For all cluster reads/queries, prefer MCP tools over `kubectl` via Bash:
- `mcp__argocd__*` — ArgoCD app status, sync, events, resource trees
- `mcp__kubernetes__*` — pods, resources, events, logs

Reserve `kubectl` via Bash for writes, port-forwards, and operations not covered by MCP.

### Conflict Resolution on PRs
Use `git rebase origin/main` (not merge) for conflict resolution, then `git push --force-with-lease`. No confirmation needed before the force-push.

## Secrets

All secrets managed via SealedSecrets (GitOps-compatible). Seal with:
```bash
kubeseal --cert <(kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key=active \
  -o jsonpath='{.items[0].data.tls\.crt}' | base64 -d) --format yaml < secret.yaml > app-credentials-sealed.yaml
```
Sealed files must be named `*-sealed.yaml` — this excludes them from yamllint (SealedSecrets contain long base64 values that fail linting) and avoids the `.gitattributes` `*secret*` git-crypt rule.

## Cluster Quick Reference

| Item | Value |
|------|-------|
| Nodes | control-plane=10.0.10.214, node01=.235, node02=.211, node03=.244, node04=.220 |
| CNI | Calico via Tigera operator + Calico APIServer |
| Mesh | Istio Ambient mode (mTLS) |
| Registry | Zot OCI registry at `registry.k8s.n37.ca` (pull-through cache + local image push target) |
| Backups | Velero → Backblaze B2 |
| Secrets | SealedSecrets (30d key rotation) |
| Policies | OPA Gatekeeper (deny mode, 5 policies, max memory limit 2Gi) |
| Updates | Renovate (weekend schedule) |
| ArgoCD | `https://argocd.k8s.n37.ca` |

## Sync Wave Order (Summary)

```
-100  tigera-operator (CNI)
 -50  argocd (self-management)
 -45/-42  istio stack
 -40  network-policies
 -35  metallb
 -30  ingress-nginx, synology-csi
 -25  sealed-secrets
 -15  kube-prometheus-stack
 -12  loki
 -11  alloy
 -10  cert-manager, external-dns, metrics-server
  -8  argo-workflows, argo-events
  -7  localstack
  -6  gatekeeper + ConstraintTemplates
  -5  gatekeeper-policies, velero, falco
  -2  zot
   0  chaos-mesh, oauth2-proxy, uptime-kuma, tempo (and most apps)
   5  lifeonabike
```

## Documentation Companion Repo

Application guides live in the `k8s-docs-n37` repo (Docusaurus site). The canonical location is the GitHub repository; `~/k8s-docs-n37` is a machine-specific local checkout path. After making significant changes to an application, update the corresponding `docs/applications/<app>.md` file there. Active branch: `docs/april-2026-updates`.
