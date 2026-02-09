# Homelab Repository Reference Guide

**Repository:** imcbeth/homelab
**Cluster:** 5x Raspberry Pi 5 (16GB each) Kubernetes Homelab

---

## Critical Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `TODO.md` | Active roadmap and priorities | Planning next tasks |
| `.claude/notes/CURRENT.md` | Recent sessions + current state | Understanding context |
| `.claude/notes/REFERENCE.md` | Stable patterns and gotchas | This file |
| `.claude/notes/sessions/` | Archived session history | Historical lookups |
| `k8s-docs-n37/docs/applications/*.md` | Application documentation | Deep-dive into specific apps |
| `manifests/applications/*.yaml` | ArgoCD Applications | Understanding deployment structure |
| `manifests/base/<app>/values.yaml` | Helm chart values | Modifying application configuration |

---

## Common Patterns

### PR-Required Workflow
- Direct pushes to `main` branch are blocked
- All changes require:
  1. Create feature branch
  2. Make changes
  3. Create PR
  4. Merge PR
  5. ArgoCD auto-deploys within ~3 minutes

### Secrets Management (Sealed Secrets)
- Most secrets managed via SealedSecrets (GitOps-compatible)
- Encrypted SealedSecret YAML files stored in Git
- Sealed Secrets controller decrypts at runtime
- Use `kubeseal` CLI to encrypt new secrets:
  ```bash
  kubeseal --cert <(kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key=active -o jsonpath='{.items[0].data.tls\.crt}' | base64 -d) --format yaml < secret.yaml > sealed-secret.yaml
  ```
- Bootstrap secrets (ArgoCD SSH key) still require manual apply
- Sealing key backed up to Synology NAS

### Multi-source ArgoCD Applications
- Chart source: Upstream Helm chart (versioned)
- Path source: Local values + custom resources
- Values file referenced via `$values/manifests/base/<app>/values.yaml`

### Kustomization Pattern (kube-prometheus-stack)
- When path source has `kustomization.yaml`, ArgoCD uses Kustomize
- Explicitly list resources to avoid parsing non-K8s files (e.g., values.yaml)
- Exclude git-crypt encrypted files

### Sync Wave Order
```
-40: network-policies (must be in place before workloads)
-35: istio-base, istio-cni (mesh foundation)
-30: sealed-secrets (must decrypt before other apps)
-25: istiod (control plane for mesh)
-20: metallb (provides LoadBalancer IPs)
-15: cert-manager (provides certificates)
-10: external-dns (manages DNS records)
 -8: argo-workflows (CI/CD automation)
 -6: gatekeeper (admission control + ConstraintTemplates)
 -5: gatekeeper-policies, synology-csi, velero, falco
  0: (default) most applications
```

---

## Known Gotchas and Solutions

| Gotcha | Solution | Reference |
|--------|----------|-----------|
| Filename matching git-crypt `*secret*` pattern | Avoid "secret" in non-secret resource filenames | 2026-01-13 |
| fsGroup in container securityContext | Use `podSecurityContext` for fsGroup, not `securityContext` | 2026-01-13 |
| SealedSecret encryption corruption | Use `kubeseal ... > file.yaml`, not copy-paste | 2026-01-14 |
| Helm-managed secrets conflict with SealedSecret | Don't use SealedSecret for Helm chart secrets | 2026-01-14 |
| Empty kustomization.yaml fails ArgoCD | Add `resources: []` for valid empty kustomization | 2026-01-13 |
| Synology CSI v1.2.1 node plugin iscsiadm regression | Use v1.2.0 for node plugin, keep sidecars upgraded | 2026-01-07 |
| Trivy ServiceMonitor not discovered by Prometheus | Use `serviceMonitor.labels` (not `additionalLabels`) with `release: kube-prometheus-stack` | 2026-01-05 |
| snapshot-controller/csi-snapshotter v8.x RBAC | Add `patch` verb for volumesnapshotcontents and groupsnapshot API group | 2026-01-11 |
| VolumeSnapshot stuck with finalizers | Use `kubectl patch` to remove finalizers | 2026-01-05 |
| Loki singleBinary + external caches | Use internal caching, disable chunksCache/resultsCache | 2026-01-05 |
| NetworkPolicy K8s API egress with Calico | Allow BOTH ClusterIP (10.96.0.1/32:443) AND control plane network (10.0.10.0/24:6443) | 2026-01-24 |
| Istio Ambient transparent proxy NetworkPolicy | HBONE port 15008 must be allowed from source namespace (not just istio-system) - source IP preserved | 2026-01-28 |
| Istio ArgoCD perpetual OutOfSync | Helm chart adds operator labels at runtime; use jqPathExpressions ignoreDifferences - cosmetic only, apps work fine | 2026-01-28 |
| Gatekeeper ConstraintTemplate/Constraint CRD ordering | Split into 2 ArgoCD Apps - templates create CRDs that constraints depend on; ArgoCD validates ALL resources before syncing | 2026-02-06 |
| ArgoCD multi-source ref+path duplicate rendering | Source with both `ref:` and `path:` renders manifests AND serves as values ref; remove `path:` from ref-only sources | 2026-02-06 |
| ServerSideApply DaemonSet drift | Must ignore ALL K8s-defaulted fields (imagePullPolicy, readinessProbe defaults, dnsPolicy, etc.) not just labels/annotations | 2026-02-05 |
| Tigera operator Installation CR drift | Operator populates finalizers and ipPool defaults at runtime; add to ignoreDifferences | 2026-02-05 |
| Application manifests not auto-deployed | `manifests/applications/*.yaml` require `kubectl apply` to update in-cluster; ArgoCD self-management doesn't manage them | 2026-02-05 |
| Promtail labeldrop after labelmap | labeldrop doesn't work after labelmap; use selective labelmap regex instead to capture only needed labels | 2026-01-28 |
| Loki 15 label limit with Istio | Istio pods have 17+ labels; use selective labelmap in promtail to stay under limit | 2026-01-28 |
| Hairpin NAT for internal probes | Pods can't reach external IPs routing back to cluster; use hostAliases to map to ClusterIP | 2026-01-29 |
| external-dns subdomain zone filtering | Use parent zone as domain-filter (n37.ca not k8s.n37.ca) - ingresses specify exact hostnames | 2026-01-25 |
| Synology CSI fsGroup race with SQLite | Add `fsGroupChangePolicy: OnRootMismatch` to podSecurityContext | 2026-01-25 |
| Loki distributed mode conflict | Set `replicas: 0` for caches explicitly | 2026-01-05 |
| Velero CSI + Kopia conflict | Use CSI exclusively, set `defaultVolumesToFsBackup: false` | 2026-01-05 |
| CSI snapshots not working | Deploy snapshot-controller alongside CSI driver | 2026-01-05 |
| values.yaml parsed as K8s manifest | Create kustomization.yaml with explicit resource list | 2025-12-27 |
| Git-crypt encrypted secrets fail in ArgoCD | Exclude from kustomization, apply manually | 2025-12-27 |
| Base64 control characters | Use `echo -n` when encoding | 2025-12-27 |
| PrometheusRule not picked up | Add `release: kube-prometheus-stack` label | 2025-12-27 |
| AlertManager smtp_auth_username_file | Use `smtp_auth_username` (plain string) instead | 2025-12-27 |
| Node-exporter unreachable | Use `hostNetwork: false`, `hostPID: true` | 2025-12-26 |

---

## Session Documentation Template

When documenting work, add to `.claude/notes/CURRENT.md`:

```markdown
### YYYY-MM-DD (Time of Day): Brief Session Title

**Completed Work:**
- Item 1
- Item 2

**Pull Requests:**
- **PR #XXX:** [Status] Description

**Issues Resolved:**
- Problem → Root Cause → Solution

**Current State:**
- What's deployed and working

**For Next Session:**
- Action items, pending work

**Files Modified:**
- List of changed files
```

---

## Architecture Overview

### Secrets Management
```
Sealed Secrets Controller (kube-system)
  └─ Decrypts SealedSecret CRDs at runtime

SealedSecrets in Git (8 total):
  ├─ manifests/base/unipoller/unipoller-sealed.yaml
  ├─ manifests/base/external-dns/cloudflare-sealed.yaml
  ├─ manifests/base/external-dns/unifi-sealed.yaml
  ├─ manifests/base/kube-prometheus-stack/alertmanager-smtp-sealed.yaml
  ├─ manifests/base/kube-prometheus-stack/snmp-exporter-sealed.yaml
  ├─ manifests/base/cert-manager/cloudflare-sealed.yaml
  ├─ manifests/base/synology-csi/client-info-sealed.yaml
  └─ manifests/base/pihole/pihole-web-sealed.yaml

Bootstrap Secret (manual apply):
  └─ secrets/argocd-git-access.yaml

Helm-Managed Secrets (auto-generated):
  └─ kube-prometheus-stack-grafana
```

### Backup Strategy
```
Velero Schedules:
  ├─ velero-daily-argocd (1:30 AM) → argocd namespace → 30 days
  ├─ velero-daily-critical-pvcs (2:00 AM) → default, loki, pihole → 30 days
  └─ velero-weekly-cluster-resources (3:00 AM Sun) → all namespaces → 90 days

Storage: Backblaze B2 (tested and validated)
```

---

## Efficiency Tips

1. **Parallel Tool Calls:** When multiple independent reads/searches needed, use parallel tool calls
2. **Use Task Tool for Exploration:** For code searches requiring multiple rounds, use Task tool with Explore agent
3. **Reference Line Numbers:** When discussing code, use `file_path:line_number` format for clarity
4. **Check Existing PRs:** Before creating new PR, verify previous PRs merged successfully
5. **Session Continuity:** Read `.claude/notes/CURRENT.md` at session start
