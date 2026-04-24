# 2026-02-27: Cluster Maintenance — Renovate Merges, Health Review & Critical Fixes

**Completed Work:**
- Expanded Falco Redis PV from 1Gi to 2Gi (was 99% full — 902M/1Gi, only 17M free)
- Live PVC patched in-cluster via online expansion (Synology iSCSI StorageClass supports it)
- Reviewed and tightened blackbox-exporter ICMP egress Calico NetworkPolicy:
  - Added `selector: app == 'blackbox-exporter'` (was applying to all pods in default namespace)
  - Narrowed destinations to exact probe targets: `10.0.1.1/32`, `10.0.1.204/32`, `8.8.8.8/32`
- Reviewed 10 open Renovate PRs, categorized by risk:
  - Merged safe batch: #464 (Velero 8.7.2→8.7.3), #463 (cert-manager 1.17.1→1.17.2), #466 (MetalLB 0.14.12→0.14.13), #467 (ingress-nginx 4.14.3→4.14.4), #470 (Loki 6.31.0→6.31.1), #471 (external-dns 1.16.1→1.16.2)
  - Closed #465 (superseded by #468)
  - Merged sequentially: #460 (kube-prometheus-stack hook fix), then #468 (kube-prometheus-stack 82.4.1→82.4.3)
  - Deferred: #469 (Istio 1.28.3→1.29.0 — major), #472 (Pi-hole 2026.02.0 — needs testing)
- Synced all ArgoCD apps after merges (cleared stuck hook jobs, handled StatefulSet VCT mismatch)
- Comprehensive cluster health review:
  - All 5 nodes healthy (22-31% memory usage)
  - 22/25 ArgoCD apps Synced+Healthy
  - 0 Gatekeeper violations
  - Identified 2 critical issues and fixed both
- **Fix #1: Falco Redis OOMKill** — Redis container CrashLoopBackOff (64 restarts), RDB dump 1288MB exceeded 1536Mi memory limit. Bumped limits (1536Mi request, 2Gi limit), added 30d TTL, maxmemory 1000mb with LRU eviction. Had to cap at 2Gi for Gatekeeper compliance (initial 2560Mi was rejected by admission webhook).
- **Fix #2: synology-csi Kustomize broken** — Kustomize patch had `namespace: synology-csi` but upstream snapshot-controller Deployment uses `namespace: kube-system`. Patch resolution happens before namespace transformation. Fixed by changing patch namespace to `kube-system`.

**Pull Requests:**
- **PR #473:** [Merged] fix: expand falco redis PV from 1Gi to 2Gi
- **PR #462:** [Merged] fix: add Calico NetworkPolicy for blackbox-exporter ICMP egress
- **PR #464, #463, #466, #467, #470, #471:** [Merged] Renovate safe batch
- **PR #460:** [Merged] fix: kube-prometheus-stack hook delete policy
- **PR #468:** [Merged] chore(deps): kube-prometheus-stack 82.4.1→82.4.3
- **PR #478:** [Merged] fix: resolve Falco Redis OOMKill and synology-csi Kustomize build
- **PR #481:** [Merged] fix: cap Falco Redis memory limit at 2Gi for Gatekeeper compliance
- **PR #482:** [Merged] chore: remove pi-hole and update Falco chart to 8.0.1
- **PR #483:** [Merged] chore: remove pi-hole application manifest
- **PR #484:** [Merged] fix: correct localstack ArgoCD project reference

**Issues Resolved:**
1. **Falco Redis PV 99% full** — Expanded PVC online from 1Gi to 2Gi.
2. **Blackbox ICMP egress blocked** — Calico NetworkPolicy with ICMP protocol support.
3. **Falco Redis OOMKill** — RDB dump exceeded container memory limit during load. Fix: bumped limits + TTL + LRU eviction to control growth.
4. **synology-csi Kustomize build failure** — Patch namespace must match upstream resource, not kustomization namespace override.
5. **Gatekeeper admission denial** — 2560Mi exceeded 2Gi max memory constraint. Capped at 2Gi.
6. **Pi-hole removed** — Not needed in cluster. App deleted, manifests removed, Renovate PR #472 closed.
7. **Falco chart updated** — 8.0.0 → 8.0.1 (patch, same app version 0.43.0).
8. **Localstack Unknown** — AppProject `applications` didn't exist. Changed to `infrastructure`.

**Key Learning:**
- StatefulSet VolumeClaimTemplates are immutable — changing Helm `storageSize` only affects future StatefulSets. Must patch live PVC separately.
- Calico NetworkPolicy `selector` uses Calico expression syntax (`app == 'blackbox-exporter'`), not K8s label selector format.
- Kustomize strategic merge patches must target the resource's original namespace (e.g. `kube-system`), not the kustomization's `namespace:` override. Namespace transformer runs AFTER patch resolution.
- Gatekeeper `container-limits` constraint caps memory at 2Gi. Always verify limits before setting above this threshold.
- Redis `maxmemory` only caps key data, not module overhead (RediSearch indexes, etc.). Container memory limit must account for both.

**Files Modified:**
- `manifests/base/falco/values.yaml` (storageSize 2Gi, memory 1536Mi/2Gi, TTL 30d)
- `manifests/base/network-policies/default/calico-network-policy-allow-egress-icmp.yaml` (scoped selector + exact targets)
- `manifests/base/network-policies/kustomization.yaml` (added ICMP policy resource)
- `manifests/base/synology-csi/patches/snapshot-controller-resources.yaml` (namespace synology-csi → kube-system)
- `manifests/applications/pi-hole.yaml` (deleted)
- `manifests/base/pihole/` (deleted — kustomization.yaml, values.yaml, pihole-web-sealed.yaml)
- `manifests/applications/falco.yaml` (chart 8.0.0 → 8.0.1)
- `manifests/applications/localstack.yaml` (project: applications → infrastructure)
