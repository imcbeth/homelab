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

| Skill | Defined in | Purpose |
|-------|-----------|---------|
| `/catch-up` | `.claude/skills/` (this repo) | Summarise recent sessions and current state |
| `/renovate-apply` | `.claude/skills/` (this repo) | Step-by-step process for applying Renovate batch PRs |
| `/cluster-shutdown` | user settings | Safe cluster shutdown procedure |
| `/cluster-healthcheck` | user settings | Validate cluster health post-startup or post-change |

Only the first two live in this repo. The other two are registered in the user's Claude Code
skill store, so they are **not version-controlled and not reviewed through PRs** — and both
have drifted from the cluster. As of 2026-10-07 `/cluster-healthcheck` still expects
`24/25` Applications (actual: 38), `5` PVCs (actual: 8), a `promtail` DaemonSet (replaced by
Alloy in 2026) and a `falco-falcosidekick-ui-redis` PVC that no longer exists. Treat its
expected-value tables as indicative and check against
[`.claude/notes/CURRENT.md`](.claude/notes/CURRENT.md), which is current.

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

## Sync Wave Order

All 38 Applications, by `argocd.argoproj.io/sync-wave`. Generated from
`manifests/applications/*.yaml` — regenerate rather than hand-edit (see below).

```
-100  tigera-operator                      (CNI, must be first)
 -50  argocd                               (self-management)
 -45  istio-base
 -44  istiod
 -42  istio-cni, istio-ztunnel
 -40  network-policies
 -38  resource-quotas
 -35  metal-lb
 -30  ingress-nginx-config, synology-csi
 -25  sealed-secrets
 -20  unipoller
 -15  kube-prometheus-stack
 -12  loki
 -11  alloy, tempo
 -10  cert-manager, external-dns, metrics-server
  -8  argo-events, argo-workflows
  -7  localstack
  -6  gatekeeper                           (+ its ConstraintTemplates)
  -5  falco, gatekeeper-policies, velero
  -4  vpa
  -3  chaos-mesh, flink-operator, oauth2-proxy
  -2  strimzi-operator, zot
   0  trivy-operator, uptime-kuma
   1  kafka
   2  flink-demo
   5  lifeonabike
```

Regenerate with:

```bash
python3 -c "
import glob, yaml
w={}
for f in glob.glob('manifests/applications/*.yaml'):
    for d in yaml.safe_load_all(open(f, encoding='utf-8')):
        if isinstance(d, dict) and d.get('kind') == 'Application':
            a = (d.get('metadata', {}).get('annotations') or {})
            w[d['metadata']['name']] = int(a.get('argocd.argoproj.io/sync-wave', 0))
for wave, name in sorted((v, k) for k, v in w.items()):
    print(f'{wave:5}  {name}')
"
```

**Use `safe_load_all`, not `safe_load`.** Several files in that directory hold multiple
documents (`istiod.yaml` among them), and `safe_load` raises on them — or, worse, a script
that catches the error silently undercounts. An earlier audit of this table missed every
multi-document file that way and reported 36 Applications instead of 38.

## Documentation Companion Repo

Application guides live in the `k8s-docs-n37` repo (Docusaurus site). The canonical location is the GitHub repository at `https://github.com/imcbeth/k8s-docs-n37`; the local checkout on this machine is `~/repos/k8s-docs-n37` (machine-specific). After making significant changes to an application, update the corresponding `docs/applications/<app>.md` file there.

**Branch from `main` and open a PR**, same as this repo — `main` is protected by a ruleset requiring one approving review. Do not name a long-lived "active branch" here: the previous entry pointed at `docs/april-2026-updates` for five months after its PRs (#77, #78, #79) had already been squash-merged.

Pre-commit in that repo runs a full `docusaurus build`, so a broken in-page anchor or unbalanced `:::admonition` fails before it is pushed.
