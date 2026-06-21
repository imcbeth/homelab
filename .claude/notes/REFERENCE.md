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
-100: tigera-operator (CNI foundation)
 -50: argocd (self-management)
 -45: istio-base (mesh CRDs)
 -44: istiod (mesh control plane)
 -42: istio-cni, istio-ztunnel (mesh data plane)
 -40: network-policies (must be in place before workloads)
 -35: metallb (provides LoadBalancer IPs)
 -30: ingress-nginx (ingress controller)
 -25: sealed-secrets (decrypt secrets)
 -10: cert-manager (provides certificates)
  -9: external-dns (manages DNS records)
  -8: argo-workflows (CI/CD automation)
  -7: localstack (S3 mock for Velero)
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
| trivy-server values path wrong | Chart uses `trivy.server.resources`, NOT `trivyServer.resources`; `trivyServer` is silently ignored | 2026-02-11 |
| StatefulSet VolumeClaimTemplate immutable | Cannot change storageClassName on existing StatefulSet; omit to match existing PVC or delete/recreate | 2026-02-11 |
| Force=true incompatible with ServerSideApply | `--force` and `ServerSideApply=true` are mutually exclusive in ArgoCD (hard error). Use normal sync. `Replace=true` IS compatible with SSA. | 2026-02-13 |
| Stale sync annotations break auto-sync | Manual `kubectl annotate` with `argocd.argoproj.io/sync: force` persists and breaks all subsequent auto-syncs. Clean up with `kubectl annotate app <name> -n argocd argocd.argoproj.io/sync- argocd.argoproj.io/sync-options-` | 2026-02-13 |
| ingress-nginx webhook job Helm keys | Chart has TWO job types: `createSecretJob.resources` and `patchWebhookJob.resources`. The `patch.resources` key controls image/pod config, NOT the container | 2026-02-14 |
| DNS egress NetworkPolicy AND vs OR | `namespaceSelector` + `podSelector` in SAME list item = AND (correct). As SEPARATE list items = OR (allows all kube-system pods, not just kube-dns) | 2026-02-14 |
| Gatekeeper denies hook jobs too | Removing a namespace from exclusion means ALL pods including Helm hook jobs need limits. Audit `redisSecretInit`, `createSecretJob`, `patchWebhookJob` etc. | 2026-02-14 |
| ArgoCD redisSecretInit resources | Top-level `redisSecretInit.resources` key (not under `redis.`). Missing limits block ArgoCD sync entirely when namespace not excluded from Gatekeeper | 2026-02-14 |
| Tigera Installation CR resource overrides | `typhaDeployment`, `csiNodeDriverDaemonSet`, `calicoKubeControllersDeployment` in Installation spec. `apiServerDeployment` in APIServer spec. | 2026-02-14 |
| Calico IPIP breaks ipBlock NetworkPolicy rules | IPIP encapsulation rewrites source IP for cross-node traffic. `ipBlock` matching node IPs only works same-node. Use bare port rules (no `from`) for API server → webhook traffic | 2026-02-15 |
| calico-apiserver CPU throttling | 100m CPU causes intermittent handler timeouts on `/apis/projectcalico.org/v3` during burst API discovery. Bumped to 250m | 2026-02-15 |
| PrometheusRule `or` with label override | Using `or` across different metric `severity` values + alert `labels.severity` override causes duplicate labelsets. Use `max by()` aggregation instead of `or` | 2026-02-15 |
| HookSucceeded race condition | `HookSucceeded` delete policy on fast jobs causes ArgoCD informer to miss completion. Use `BeforeHookCreation` — keeps job until next sync | 2026-02-15 |
| ArgoCD stuck operation — two fields | Clear BOTH `/status/operationState` AND `/operation` (pending ops). Auto-sync creates `/operation` which races with manual sync | 2026-02-15 |
| Auto-sync exponential backoff | After repeated failures, auto-sync enters backoff. Clear `/operation` and trigger manual sync, or wait | 2026-02-15 |
| MetalLB speaker has 7 containers | Main `speaker.resources` + `frr`, `reloader`, `frrMetrics`, and 3 init containers (`cpFrrFiles`, `cpReloader`, `cpMetrics`). All need limits for Gatekeeper | 2026-02-15 |
| cert-manager Application not applied | Limits existed in git Application spec but were never `kubectl apply`'d. Always apply Application manifests post-merge | 2026-02-15 |
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
| Kustomize patch namespace must match upstream | Patches target resources by ID (name+namespace). Must use upstream namespace (e.g. `kube-system`), not kustomization `namespace:` override. Namespace transformer runs AFTER patch resolution | 2026-02-27 |
| Gatekeeper max memory limit is 2Gi | `container-limits` constraint caps memory at 2Gi. Always check before setting limits above this threshold | 2026-02-27 |
| Redis-stack module memory overhead | `maxmemory` only caps key data, not module overhead (RediSearch, TimeSeries, etc.). Container limit must account for both. Use TTL + maxmemory-policy to control growth | 2026-02-27 |
| bitnami/kubectl image has no python3 | Image includes kubectl, jq, curl, bash, awk — NOT python3 or wget. Use jq for JSON construction in CronJob scripts | 2026-03-01 |
| CronJob specs not updating via apply | `kubectl apply` may not update CronJob spec. Delete then apply to force update | 2026-03-01 |
| ModSecurity WAF impractical on Pi | OWASP CRS requires ~512-768Mi memory, exceeds 256Mi ingress-nginx limit. Not justified for private 10.0.10.0/24 network | 2026-03-01 |
| ArgoCD prune+SSA recreates PVCs on chart upgrade | `prune: true` + SSA deletes and reprovisions PVCs → new iSCSI LUN, old LUN orphaned on NAS. Fix for standalone PVCs: `argocd.argoproj.io/sync-options: Prune=false` annotation (via `persistence.annotations` in values). Fix for StatefulSet VCTs: `ignoreDifferences: .spec.volumeClaimTemplates`. See `docs/troubleshooting/argocd-pvc-protection.md` | 2026-04-17 |
| Released PVs = orphaned iSCSI LUNs | Retain policy keeps LUN on NAS indefinitely. Each Released PV wastes NAS storage. Audit `kubectl get pv \| grep Released` regularly. Delete PV object AND manually delete LUN in DSM iSCSI Manager. | 2026-04-17 |
| iSCSI "Portal doesn't exist" NAS warning | Released PV whose NAS target is broken/deleted + stale `/etc/iscsi/nodes/` entry on node. Fix: delete NAS LUN from DSM, `kubectl delete pv`, remove stale entry via `kubectl exec -n synology-csi <node-pod> -c csi-plugin -- rm -rf /host/etc/iscsi/nodes/<iqn>`. See `docs/troubleshooting/iscsi-synology.md` | 2026-04-17 |
| iSCSI REOPEN loop | NAS session stale after network blip. Fix: DSM disable+re-enable target, then `kubectl delete volumeattachment <name>` to force clean detach/re-attach cycle. Data is never at risk. | 2026-04-17 |
| Kustomize remote resource + resource limits patch | `resources: [https://raw.githubusercontent.com/...]` in kustomization.yaml fetches upstream at sync time. Use strategic merge patch to add fields (e.g. resource limits) to upstream Deployments without forking. Consolidates multi-source ArgoCD Application to single Kustomize source. | 2026-04-17 |
| apiextensions/v1 CRD field defaulting | Server-side defaults `additionalPrinterColumns[].priority=0` and `spec.conversion.strategy=None`. Any CRD-shipping chart that goes OutOfSync indefinitely is probably hitting one of these. Add both to `ignoreDifferences` | 2026-06-04 |
| Orphan VolumeSnapshotContents hammer DSM | `synology-csi-snapshotter` retries every error VSC every reconcile. 283 orphans from old DR tests pegged NAS CPU at 100%. `vsc-orphan-janitor` CronJob prevents recurrence (PR #724) | 2026-06-04 |
| ArgoCD selfHeal does NOT restore `.spec.replicas` drift | Manual `kubectl scale` mutates the spec. `argocd-application-controller` doesn't hold SSA ownership of `.spec.replicas`, so the drift is invisible to selfHeal. After cluster shutdown, MANUALLY re-scale workloads back up — symmetric to shutdown sequence | 2026-06-04 |
| Pod-to-MetalLB VIP hairpin | `KUBE-EXT` chain only DNATs LoadBalancer VIPs for `src-type LOCAL`. Pod traffic silently drops. Non-meshed pods MUST use ClusterIP DNS. Meshed pods work via ztunnel HBONE bypass | 2026-06-02 |
| HBONE bypass requires BOTH ends ambient-meshed | Traffic from meshed pod to non-meshed pod is direct TCP (no HBONE), so bare port 15008 ingress rule on destination is irrelevant. Destination must allow source pod IP on the actual application port | 2026-06-02 |
| NetworkPolicy fixes need both directions — INCLUDING same-namespace | When policy declares Egress, same-ns pod-to-pod is DENIED without explicit intra-ns rule. Hit 5 times during PVC RO automation series (#736, #738, #739, #746, #747, #763). Cross-component path checklist: src egress + dst ingress + intra-ns rule (if same-ns) + HBONE (if mesh) | 2026-06-21 |
| `/host/proc/mounts` is per-container, not host | Symlinks to `/proc/self/mounts` resolving to reader's mount ns. Use `/host/proc/1/mounts` to get HOST init's mount table regardless of PID namespace | 2026-06-05 |
| ArgoCD "Synced + Healthy" ≠ "applied + working" | (1) SSA field-ownership disagreements can leave cluster in pre-change state silently (PR #739 broken NetPol never propagated). (2) For CronJobs, ArgoCD checks resource exists, not whether the Jobs actually succeed (16-day silent outage). Always verify NetworkPolicy with `kubectl get` after sync; alert on Job success independently | 2026-06-07 |
| Don't build auto-remediation depending on system being remediated | The PVC RO remediator queried Prometheus → silent no-op for 16 days when Prom's PVC went RO. Solution: query source of truth as directly as possible. Monitor pods' `/metrics` has no upstream dependencies (PR #753) | 2026-06-21 |
| `set -e` + `grep` no-match is a trap | `grep` exits 1 on no match. Cluster-healthy state IS no-match. With `set -e`, healthy case looks identical to script failure. Always `|| true` the no-match path. Caused remediator to silently fail every healthy run (PR #764) | 2026-06-21 |
| iSCSI globalmount RO independent of pod-mount RO | A pod's CSI mount is a bind-mount of the CSI driver's globalmount. If globalmount itself is RO, pod-delete creates fresh pod that bind-mounts the same RO globalmount. Fix: cross-node reschedule (cordon + delete pod → schedules elsewhere → CSI does fresh attach) | 2026-06-21 |
| CronJob `failedJobsHistoryLimit` affects forensics | Default 3 means at 2-min cadence you have 6 min of failure history. Useful for normal debugging, useless for a 16-day silent incident. Bump to ~50 for incident retention | 2026-06-21 |
| Renovate chart minor bumps may need manual sync | istio 1.30.1 chart CRDs got label updates (`helm.sh/chart: base-1.30.0 → 1.30.1`); auto-sync didn't pick them up. `kubectl patch` operation with `prune: true` cleared the drift. Watch for this on any chart bump that touches CRDs | 2026-06-21 |
| Chart switching RollingUpdate → Recreate | Argo-events 2.4.22 chart switched strategy. Existing Deployment retains K8s-defaulted `rollingUpdate` fields that SSA can't remove (not owned by argocd-controller). Fix: `kubectl delete deployment <name>` — ArgoCD recreates clean | 2026-06-21 |
| Bitnami chart repo URL discontinued | `bitnami-labs.github.io/sealed-secrets` returning 404 (chart repo URL may have moved). Runtime controller still healthy but ArgoCD can't reconcile. Check `bitnamicharts.com` redirects or pin chart locally | 2026-06-21 |

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
  └─ manifests/base/synology-csi/client-info-sealed.yaml

Bootstrap Secret (manual apply):
  └─ secrets/argocd-git-access.yaml

Helm-Managed Secrets (auto-generated):
  └─ kube-prometheus-stack-grafana
```

### Backup Strategy
```
Velero Schedules:
  ├─ velero-daily-argocd (1:30 AM) → argocd namespace → 30 days
  ├─ velero-daily-critical-pvcs (2:00 AM) → default, loki, trivy-system, falco → 30 days
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
