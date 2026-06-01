# 2026-05-31 (Evening): Renovate Batch, Zot StatefulSet Fix, MetalLB frr-k8s Disable

**Context:** Resumed from previous context mid-session (session archiving + Renovate batch were already complete). Picked up at the MetalLB frr-k8s Gatekeeper blocking issue.

## Completed Work

**MetalLB 0.16 frr-k8s Gatekeeper fix (PR #652, merged):**
- MetalLB 0.16 enabled the `frr-k8s` BGP backend by default, deploying `metallb-frr-k8s` DaemonSet (5 nodes) + `metallb-frr-k8s-statuscleaner` Deployment. Both blocked by OPA Gatekeeper `require-resource-limits` — DaemonSet has 4 init containers (`cp-frr-files`, `cp-reloader`, `cp-metrics`, `cp-frr-status`) with NO chart-level resource configuration.
- Cluster uses L2 mode exclusively (`L2Advertisement`, no `BGPAdvertisement`). Set `frrk8s.enabled: false` in `manifests/base/metal-lb/metallb-metrics-yaml` — cleanly removes both components without any Gatekeeper namespace exclusions.
- After merge: `kubectl apply -f manifests/applications/metal-lb.yaml` → `metal-lb Synced Healthy` ✅

**Zot StatefulSet serviceName fix (PR #651, merged):**
- zot chart 0.1.116 removed `spec.serviceName` from the StatefulSet template. ArgoCD (as SSA field manager `argocd-controller`) previously owned this field. Releasing SSA field ownership triggers Kubernetes StatefulSet admission controller ("spec: Forbidden: updates to statefulset spec for fields other than 'replicas'...")
- Added `ignoreDifferences` for `.spec.serviceName` + `RespectIgnoreDifferences=true` to zot ArgoCD Application — but this did NOT fix the issue. SSA managed-field release still triggers the admission check regardless.
- **Real fix:** Deleted the StatefulSet (`kubectl delete statefulset zot -n zot --wait=false`). ArgoCD immediately recreated it from chart 0.1.116 (without `serviceName`). PVC `zot-pvc-zot-0` (50Gi iSCSI, `synology-iscsi-delete`) survived — VCT PVCs are not tracked by ArgoCD and not deleted when StatefulSet is removed. New pod came up `1/1 Running` within ~7 minutes.
- After merge: `kubectl apply -f manifests/applications/zot.yaml` → StatefulSet delete → `zot Synced Healthy` ✅

**Key Gotchas Discovered:**
- **`RespectIgnoreDifferences` doesn't prevent SSA managed-field release errors**: When a chart REMOVES an immutable field, ArgoCD releases SSA field manager ownership. Even with `RespectIgnoreDifferences=true`, Kubernetes StatefulSet admission controller validates the managed-fields change and rejects it. The only fix for this pattern is StatefulSet delete + recreate.
- **frr-k8s subchart init containers have no resource config**: `frr-k8s` chart init containers (`cp-frr-files`, `cp-reloader`, `cp-metrics`, `cp-frr-status`) copy binaries at startup and cannot have resources configured via Helm values. Gatekeeper `require-resource-limits` blocks the DaemonSet pods. If BGP mode is not needed, `frrk8s.enabled: false` is the cleanest solution.
- **StatefulSet VCT PVCs survive StatefulSet deletion**: Kubernetes does not auto-delete VCT-created PVCs when a StatefulSet is deleted. The new StatefulSet picks up the existing PVC by name (`<vctName>-<stsName>-<ordinal>`). ArgoCD with `prune: true` does not delete them either (VCT PVCs are not in ArgoCD's tracked resources).

**Second Renovate batch (8 PRs, merged same evening):**
- Merged: #641 (alloy 1.8.2), #643 (external-snapshotter 8.6.0), #644 (oauth2-proxy chart 10.6.0), #645 (istio 1.30.0), #646 (prometheus 3.12.0), #647 (csi-attacher 4.12.0), #648 (csi-node-driver-registrar 2.17.0), #649 (synology-csi 1.3.0)
- Applied: `kubectl apply` for istio-base/cni/istiod, alloy, oauth2-proxy (all changed Application manifests); synology-csi auto-synced via base/
- Skipped then fixed #642 + #650 (see below)
- All apps Synced+Healthy post-batch (flink-operator CRD drift pre-existing, not related)

**Third pass — flink-operator 1.15.0 + Flink Dockerfile 2.2 (PRs #642, #650, #656):**
- **#642** (flink-operator image 1.15.0) + **#656** (chart URL `1.14.0` → `1.15.0` archive): merged together so chart CRDs and operator binary stay in sync. Applied `kubectl apply -f manifests/applications/flink-operator.yaml`. Pod immediately rolled to `apache/flink-kubernetes-operator:1.15.0` ✅
- **#650** (Flink Dockerfile `1.20-java17` → `2.2-java17`): merged. No immediate cluster impact — running FlinkDeployments use pre-built `registry.k8s.n37.ca/flink-demo:1.0.0`. Next image rebuild will use Flink 2.2 and will need PyFlink pipeline testing against Flink 2.x APIs.
- **All Renovate PRs closed.** No open Renovate PRs remain.

**Also completed earlier in this context window (session archiving + first Renovate batch):**
- Archived 5 oldest sessions from CURRENT.md into `sessions/` files
- Created kafka.md and flink.md guides in k8s-docs-n37 (PRs #640 and #81, merged)
- Merged 10 Renovate PRs (#619–#628) with `--admin` bypass; applied all Application manifests
- ArgoCD self-upgrade completed during batch (repo-server cycled, auto-recovered)
- Zot 0.1.116 Renovate PR triggered the serviceName issue investigated above

## Pull Requests

- **PR #651:** [Merged] fix: ignore zot StatefulSet serviceName removed in chart 0.1.116
- **PR #652:** [Merged] fix(metallb): disable frr-k8s backend (L2-only cluster)
