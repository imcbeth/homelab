### 2026-01-28 (Late Night): Promtail Label Limit Fix

**Completed Work:**
- Fixed promtail errors: "has 17 label names; limit 15"
- Istio pods (ztunnel, istio-cni-node) have 17+ Kubernetes labels
- Initial `labeldrop` approach failed (relabel_configs process original labels)
- Implemented selective `labelmap` to only capture essential labels

**Pull Requests:**
- **PR #324:** [Merged] fix: Drop noisy labels in promtail (didn't work)
- **PR #325:** [Merged] fix: Use selective labelmap in promtail for Loki label limit

**Key Learning:**
Promtail `labeldrop` in relabel_configs doesn't work after `labelmap` because relabel_configs process against the original label set, not transformed labels. Solution: use selective `labelmap` regex to only capture needed labels.

**Files Modified:**
- `manifests/base/promtail/values.yaml`

---

### 2026-01-28 (Evening): Istio ArgoCD Sync Fixes

**Completed Work:**
- Added `ignoreDifferences` to Istio ArgoCD applications for webhook caBundle drift
- Switched from jsonPointers to jqPathExpressions for broader label/annotation matching
- Added RespectIgnoreDifferences sync option
- Cleaned up temporary `istio-1.24.2/` directory

**Pull Requests:**
- **PR #320:** [Merged] docs: Update CURRENT.md with Istio Ambient session
- **PR #321:** [Merged] fix: Add ignoreDifferences for Istio webhook drift
- **PR #322:** [Merged] fix: Improve Istio ignoreDifferences with jqPathExpressions

**Key Learning:**
Istio's Helm chart dynamically adds labels like `install.operator.istio.io/owning-resource` and `operator.istio.io/component` that cause perpetual drift. Using `jqPathExpressions` with broad label ignores helps but doesn't fully resolve. The apps function correctly despite the OutOfSync status.

**Files Modified:**
- `manifests/applications/istio-base.yaml` (ignoreDifferences)
- `manifests/applications/istio-cni.yaml` (ignoreDifferences + RespectIgnoreDifferences)
- `manifests/applications/istiod.yaml` (ignoreDifferences + RespectIgnoreDifferences)
