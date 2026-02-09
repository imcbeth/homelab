# 2025-12-27 (Evening): Loki + Promtail Production Hardening and Fixes

**Completed Work:**
- Fixed persistent ArgoCD StatefulSet OutOfSync issues with jqPathExpressions
- Enabled Prometheus metrics collection for Loki and Promtail
- Added control-plane toleration for complete log coverage

**Pull Requests:**
- **PR #87:** [Merged] Fix: Use jqPathExpressions for StatefulSet sync and enable metrics
- **PR #89:** [Merged] Fix: Add control-plane toleration to Promtail DaemonSet

**Issue 1: ArgoCD StatefulSet Persistent OutOfSync**

Solution using jqPathExpressions with wildcards:
```yaml
syncOptions:
  - RespectIgnoreDifferences=true

ignoreDifferences:
  - group: "apps"
    kind: "StatefulSet"
    jqPathExpressions:
      - .spec.volumeClaimTemplates[]?.status
      - .spec.volumeClaimTemplates[]?.metadata.creationTimestamp
      - .status
```

Why: `jsonPointers` only matches exact paths; `jqPathExpressions` uses `[]?` wildcard for ANY array index.

**Issue 2: Missing Control-Plane Logs**

Added toleration to Promtail DaemonSet:
```yaml
tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
```

Benefits: Promtail now runs on ALL 5 nodes, collecting logs from kube-apiserver, kube-controller-manager, kube-scheduler, etcd, CoreDNS.

**Key Lessons:**
1. Use jqPathExpressions for arrays/dynamic structures
2. Always add `RespectIgnoreDifferences=true` with auto-sync
3. ServiceMonitor labels must include `release: kube-prometheus-stack`
4. DaemonSets for system components need control-plane tolerations

**Files Modified:**
- `manifests/applications/loki.yaml` - ignoreDifferences with jqPathExpressions
- `manifests/base/loki/values.yaml` - Enabled ServiceMonitor
- `manifests/base/promtail/values.yaml` - Enabled ServiceMonitor, added toleration
