### 2026-02-11: Resource Right-Sizing Audit

**Completed Work:**
- Audited actual memory usage vs configured requests/limits across all workloads
- Fixed 5 under-provisioned containers at OOM risk: sealed-secrets, promtail (x5), loki sidecar, grafana sidecars (x2)
- Fixed falco redis-stack at 96% of limit: bumped to 1Gi/1536Mi, maxmemory 800mb to 1000mb
- Reduced over-provisioned velero: 256Mi/512Mi to 128Mi/256Mi
- Fixed trivy-server value path bug: `trivyServer.resources` is not a valid chart key, moved to `trivy.server.resources`
- Fixed trivy-server StatefulSet sync failure caused by storageClassName change on existing VCT
- Added Force=true sync option to kube-prometheus-stack webhook patch job
- Cleaned up stale git stashes

**Pull Requests:**
- **PR #423:** [Merged] chore: right-size container memory requests and limits
- **PR #424:** [Merged] fix: remove storageClassName from trivy-server to unblock StatefulSet sync
- **PR #425:** [Merged] fix: add Force=true sync option to kube-prometheus-stack webhook patch job

**Issues Resolved:**
1. **trivy-server values ignored** - `trivyServer.resources` is not a valid chart key for trivy-operator 0.31.0. Correct path is `trivy.server.resources`. In-cluster was using chart defaults (512Mi/1Gi) instead of configured 64Mi/256Mi.
2. **trivy-server StatefulSet sync failure** - Adding `storageClassName` to an existing StatefulSet VolumeClaimTemplate is forbidden by Kubernetes. Fix: omit storageClassName to match existing PVC.
3. **kube-prometheus-stack webhook patch job conflict** - Job already exists from previous sync. Fix: `argocd.argoproj.io/sync-options: Force=true`.

**Verification:**
- All 7 workloads confirmed with correct resources in-cluster
- All 24 ArgoCD apps Synced/Healthy
- Zero OOM events, zero Gatekeeper violations

**Files Modified:**
- `manifests/base/sealed-secrets/values.yaml` (memory 32Mi/64Mi to 64Mi/128Mi)
- `manifests/base/promtail/values.yaml` (memory 64Mi/128Mi to 128Mi/256Mi)
- `manifests/base/loki/values.yaml` (sidecar request 64Mi to 128Mi)
- `manifests/base/kube-prometheus-stack/values.yaml` (sidecar request 64Mi to 128Mi)
- `manifests/base/falco/values.yaml` (redis 512Mi/1Gi to 1Gi/1536Mi, maxmemory 1000mb)
- `manifests/base/velero/values.yaml` (memory 256Mi/512Mi to 128Mi/256Mi)
- `manifests/base/trivy-operator/values.yaml` (fixed value path, removed storageClassName)
- `manifests/applications/kube-prometheus-stack.yaml` (Force=true sync option)
