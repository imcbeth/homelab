### 2026-02-13 (Evening): Istio Prometheus ServiceMonitors

**Completed Work:**
- Added ServiceMonitor for istiod (port 15014/http-monitoring, 30s interval)
- Added PodMonitor for ztunnel (port 15020/ztunnel-stats, 30s interval)
- Used kube-prometheus-stack `additionalServiceMonitors`/`additionalPodMonitors` to avoid ArgoCD ref+path duplicate rendering
- Verified: istiod 1 target up, ztunnel 5 targets (all nodes) up
- Network policies already permitted scraping — only monitor resources were missing

**Pull Requests:**
- **PR #428:** [Merged] feat: add Prometheus monitors for istiod and ztunnel
- **PR #434:** [Merged] fix: add bearer token auth to metrics-server ServiceMonitor
- **PR #435:** [Merged] feat: add Istio service mesh section to APM dashboard (7 panels)

**Issues Resolved:**
1. **metrics-server 403 Forbidden** — ServiceMonitor was missing `bearerTokenFile`. metrics-server requires Kubernetes API bearer token auth to serve `/metrics`. Fix: added `bearerTokenFile: /var/run/secrets/kubernetes.io/serviceaccount/token` (same pattern as kubelet ServiceMonitor). PR #434.

**Files Modified:**
- `manifests/base/kube-prometheus-stack/values.yaml` (additionalServiceMonitors + additionalPodMonitors)
- `manifests/base/metrics-server/servicemonitor.yaml` (added bearerTokenFile for auth)
- `manifests/base/grafana/dashboards/apm-dashboard.yaml` (added Istio Service Mesh section, 7 panels)
