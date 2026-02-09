# 2025-12-26 (Evening): Prometheus Monitoring Stack Fixes

**Completed Work:**
- Fixed node-exporter scraping issue (all 5 nodes now monitored)
- Fixed Grafana Multi-Attach PVC errors during ArgoCD updates
- Disabled unreachable control plane component monitoring
- Cleaned up Prometheus targets

**Pull Requests:**
- **PR #72:** [Merged] Disable hostNetwork for node-exporter
- **PR #73:** [Merged] Set Grafana deployment strategy to Recreate
- **PR #74:** [Merged] Explicitly set rollingUpdate to null
- **PR #75:** [Merged] Disable unreachable control plane ServiceMonitors

**Issues Resolved:**

1. **Node-Exporter Scraping Failures**
   - Problem: Only 1/5 node-exporters scraped
   - Root Cause: `hostNetwork: true` + Calico CNI routing limitation
   - Solution: Changed to `hostNetwork: false`, kept `hostPID: true`
   - Result: All 5 node-exporters now UP via pod IPs

2. **Grafana Multi-Attach PVC Errors**
   - Problem: ArgoCD updates failed with volume already attached
   - Root Cause: `ReadWriteOnce` PVC + `RollingUpdate` strategy conflict
   - Solution: Changed to `Recreate` strategy with `rollingUpdate: null`

3. **Control Plane Component Scraping Failures**
   - Problem: kube-controller-manager, kube-etcd, kube-proxy failing
   - Root Cause: Components bind to localhost in kubeadm
   - Solution: Disabled ServiceMonitors for these components

**Key Lessons:**
- Calico CNI cannot route to hostNetwork pods via node IPs across nodes
- node-exporter only needs hostPID, not hostNetwork
- ReadWriteOnce PVCs require Recreate strategy for clean updates

**Files Modified:**
- `manifests/base/kube-prometheus-stack/values.yaml`
  - node-exporter: `hostNetwork: false`, `hostPID: true`
  - grafana: `deploymentStrategy.type: Recreate`
  - kubeControllerManager, kubeEtcd, kubeProxy: `enabled: false`
