# Claude Code - Homelab Repository Guide

## Quick Reference for AI Assistants Working in This Repository

**Last Updated:** 2025-12-27
**Repository:** imcbeth/homelab
**Cluster:** 5x Raspberry Pi 5 (16GB each) Kubernetes Homelab

---

## 📋 Recent Updates

### 2025-12-27 (Evening): Loki + Promtail Production Hardening and Fixes

**Completed Work:**
- ✅ Fixed persistent ArgoCD StatefulSet OutOfSync issues with jqPathExpressions
- ✅ Enabled Prometheus metrics collection for Loki and Promtail
- ✅ Added control-plane toleration for complete log coverage
- ✅ Created comprehensive documentation in k8s-docs-n37

**Pull Requests:**
- **PR #85:** [Merged] Fix: Ignore creationTimestamp in Loki ArgoCD sync
- **PR #86:** [Merged] Fix: Add StatefulSet-specific ignoreDifferences for Loki
- **PR #87:** [Merged] Fix: Use jqPathExpressions for StatefulSet sync and enable metrics
- **PR #89:** [Merged] Fix: Add control-plane toleration to Promtail DaemonSet
- **k8s-docs-n37 PR #9:** [Merged] Add comprehensive Loki + Promtail application guide
- **k8s-docs-n37 PR #10:** [Merged] Update Loki guide with control-plane and metrics details

**Issue 1: ArgoCD StatefulSet Persistent OutOfSync**

After initial deployment, Loki StatefulSet showed as OutOfSync with `creationTimestamp: null` differences.

**Troubleshooting Journey:**

**Attempt 1 (PR #85):** Added basic ignoreDifferences
```yaml
ignoreDifferences:
  - group: "*"
    kind: "*"
    jsonPointers:
      - /metadata/creationTimestamp
```
**Result:** Still OutOfSync - StatefulSet has additional fields

**Attempt 2 (PR #86):** Added StatefulSet-specific jsonPointers
```yaml
- group: "apps"
  kind: "StatefulSet"
  jsonPointers:
    - /spec/volumeClaimTemplates/0/metadata/creationTimestamp
    - /spec/volumeClaimTemplates/0/status
    - /status
```
**Result:** Still OutOfSync - only matches index 0

**Root Cause Identified:**
The volumeClaimTemplates has `status.phase: Pending` field that Kubernetes auto-generates. The `jsonPointers` approach with `/spec/volumeClaimTemplates/0/status` only matches the first array element (index 0), but StatefulSets can have dynamic indices.

**Final Solution (PR #87):** Use jqPathExpressions with wildcards
```yaml
syncOptions:
  - RespectIgnoreDifferences=true  # Honor ignore rules during auto-sync

ignoreDifferences:
  - group: "apps"
    kind: "StatefulSet"
    jqPathExpressions:
      - .spec.volumeClaimTemplates[]?.status                      # ALL array elements
      - .spec.volumeClaimTemplates[]?.metadata.creationTimestamp
      - .status
```

**Why jqPathExpressions Works:**
- `jsonPointers`: Only matches exact paths like `/spec/volumeClaimTemplates/0/status`
- `jqPathExpressions`: Uses `[]?` wildcard to match ANY array index
- Handles dynamic StatefulSet configurations

**Verification:**
```bash
kubectl get application loki -n argocd -o jsonpath='{.status.sync.status}'
# Returns: Synced
```

**Issue 2: No Metrics from Loki or Promtail**

User reported logs were flowing but no metrics appeared in Prometheus.

**Root Cause:**
ServiceMonitors were disabled in both Loki and Promtail values.yaml files.

**Solution (PR #87):**
Enabled ServiceMonitor with proper labels for Prometheus auto-discovery:

**Loki:**
```yaml
monitoring:
  serviceMonitor:
    enabled: true
    labels:
      release: kube-prometheus-stack  # For ServiceMonitor discovery
```

**Promtail:**
```yaml
serviceMonitor:
  enabled: true
  labels:
    release: kube-prometheus-stack
```

**Metrics Now Available:**

**Loki Metrics:**
```promql
# Logs ingested per second
rate(loki_distributor_lines_received_total[5m])

# Active log streams
loki_ingester_streams

# Query performance (99th percentile)
histogram_quantile(0.99, rate(loki_request_duration_seconds_bucket[5m]))

# Storage usage
loki_store_chunk_entries
```

**Promtail Metrics (per pod × 5):**
```promql
# Logs sent to Loki
rate(promtail_sent_entries_total[5m])

# Bytes read from log files
rate(promtail_read_bytes_total[5m])

# Active scrape targets (should show ~250 pods)
promtail_targets_active_total
```

**Issue 3: Missing Control-Plane Logs**

User noticed Promtail was only running on 4/5 nodes - missing the control-plane.

**Investigation:**
```bash
kubectl get pods -n loki -l app.kubernetes.io/name=promtail -o wide
# Showed: node01, node02, node03, node04
# Missing: control-plane

kubectl get nodes -o json | python3 -c "import sys, json; nodes = json.load(sys.stdin)['items']; [print(f\"{n['metadata']['name']}: {n['spec'].get('taints', [])}\") for n in nodes]"
# control-plane: [{'effect': 'NoSchedule', 'key': 'node-role.kubernetes.io/control-plane'}]
```

**Root Cause:**
Control-plane node has `node-role.kubernetes.io/control-plane:NoSchedule` taint that prevents regular DaemonSet pods from scheduling.

**Solution (PR #89):**
Added toleration to Promtail DaemonSet:
```yaml
tolerations:
  - key: node-role.kubernetes.io/control-plane
    operator: Exists
    effect: NoSchedule
```

**Benefits:**
- Promtail now runs on ALL 5 nodes (4 workers + 1 control-plane)
- Collects logs from critical control plane components:
  - kube-apiserver
  - kube-controller-manager
  - kube-scheduler
  - etcd
  - CoreDNS

**Query Control-Plane Logs:**
```logql
{node="control-plane"}               # All control-plane logs
{pod=~"kube-apiserver.*"}           # API server
{pod=~"etcd.*"}                     # etcd
{pod=~"kube-controller-manager.*"}  # Controller manager
{pod=~"kube-scheduler.*"}           # Scheduler
```

**Documentation Created:**

**k8s-docs-n37 PR #9:** Comprehensive 568-line Loki + Promtail application guide
- Architecture overview and component details
- LogQL query examples (basic to advanced)
- Common use cases and troubleshooting patterns
- Performance tuning for Raspberry Pi cluster
- Grafana dashboard recommendations
- Security considerations and upgrade procedures

**k8s-docs-n37 PR #10:** Updated guide with control-plane and metrics
- Control-plane toleration documentation
- ServiceMonitor enablement details
- Complete Prometheus metrics reference
- 5-node coverage verification

**Files Modified:**
- `manifests/applications/loki.yaml` - ignoreDifferences with jqPathExpressions
- `manifests/base/loki/values.yaml` - Enabled ServiceMonitor
- `manifests/base/promtail/values.yaml` - Enabled ServiceMonitor, added control-plane toleration

**Current State:**
- ✅ Loki StatefulSet: Synced in ArgoCD
- ✅ Loki metrics: Available in Prometheus
- ✅ Promtail metrics: Available in Prometheus (5 pods)
- ✅ Log collection: All 5 nodes including control-plane
- ✅ Grafana datasource: Working
- ✅ Documentation: Complete in k8s-docs-n37

**Key Lessons Learned:**

1. **jsonPointers vs jqPathExpressions:**
   - Use jsonPointers for simple, fixed paths
   - Use jqPathExpressions for arrays or dynamic structures
   - Always add RespectIgnoreDifferences=true with auto-sync

2. **ServiceMonitor Labels Matter:**
   - Must include `release: kube-prometheus-stack` label
   - Prometheus Operator uses label selectors for discovery
   - Check with: `kubectl get servicemonitor -n loki -o yaml`

3. **DaemonSet Tolerations:**
   - Control-plane nodes have standard taints
   - System DaemonSets (node-exporter, Promtail) need tolerations
   - Use `operator: Exists` for flexibility

4. **ArgoCD Sync Troubleshooting:**
   - Check: `kubectl get application <name> -n argocd -o yaml`
   - Look at `.status.sync.status` and `.status.conditions`
   - For StatefulSets, check volumeClaimTemplates and status fields

**Verification Commands:**
```bash
# ArgoCD sync status
kubectl get application loki -n argocd -o jsonpath='{.status.sync.status}'
kubectl get application promtail -n argocd -o jsonpath='{.status.sync.status}'

# ServiceMonitors
kubectl get servicemonitor -n loki

# Promtail distribution
kubectl get pods -n loki -l app.kubernetes.io/name=promtail -o wide

# Metrics in Prometheus
# Port-forward: kubectl port-forward -n default svc/kube-prometheus-stack-prometheus 9090:9090
# Navigate to: http://localhost:9090/targets
# Look for: serviceMonitor/loki/loki and serviceMonitor/loki/promtail

# Query logs in Grafana
# Port-forward: kubectl port-forward -n default svc/kube-prometheus-stack-grafana 3000:80
# Navigate to: http://localhost:3000 → Explore → Loki
# Query: {namespace="default"}
```

---

### 2025-12-26 (Post-Midnight): Deploy Loki + Promtail Log Aggregation Stack

**Completed Work:**
- ✅ Deployed Grafana Loki in SingleBinary mode for centralized log aggregation
- ✅ Deployed Promtail DaemonSet (5 pods, one per node) for log collection
- ✅ Fixed initial deployment issue (Promtail not included in Loki chart v6.x)
- ✅ Configured Grafana datasource auto-discovery
- ✅ Implemented TODO.md Platform Enhancement #7: Log Aggregation

**Pull Requests:**
- **PR #83:** [Merged] Deploy Loki + Promtail logging stack
- **PR #84:** [Ready] Fix: Add Promtail deployment for log collection

**Architecture Deployed:**

```
┌─────────────────────────────────────────┐
│  Promtail DaemonSet (5 pods)            │
│  - One pod per Pi node                  │
│  - Collects logs from /var/log/pods/    │
│  - 50m/100m CPU, 64Mi/128Mi memory each │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Loki SingleBinary (1 pod)              │
│  - Storage: 20Gi PVC on Synology        │
│  - Retention: 7 days (168h)             │
│  - 200m/500m CPU, 384Mi/768Mi memory    │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Grafana (auto-discovered datasource)   │
│  - Query logs via LogQL                 │
│  - Dashboards and exploration           │
└─────────────────────────────────────────┘
```

**Configuration Details:**

**Loki (SingleBinary Mode):**
- Chart: `grafana/loki` version 6.49.0
- Sync Wave: -12 (after kube-prometheus-stack -15)
- Namespace: `loki`
- Storage: 20Gi PVC on `synology-iscsi-retain`
- Retention: 7 days with compaction every 10 minutes
- Schema: v13 (TSDB store)
- Resources: 200m/500m CPU, 384Mi/768Mi memory

**Promtail (DaemonSet):**
- Chart: `grafana/promtail` version 6.16.6
- Sync Wave: -11 (after Loki -12)
- Namespace: `loki`
- Replicas: 5 (one pod per node)
- Resources per pod: 50m/100m CPU, 64Mi/128Mi memory
- hostNetwork: false (avoids Calico CNI issues)
- hostPID: true (access to /var/log/pods/)

**Log Collection:**
- Scrapes all running Kubernetes pods
- Log path: `/var/log/pods/`
- Labels added: namespace, pod, container, node
- Client URL: `http://loki.loki.svc.cluster.local:3100/loki/api/v1/push`

**Issue Discovered During Deployment:**

After initial deployment (PR #83), user reported only seeing loki-canary pod logs in Grafana:

**Troubleshooting:**
```bash
# 1. Check pods in loki namespace
kubectl get pods -n loki -o wide
# Found: loki-0, loki-canary pods, caches - but NO Promtail pods

# 2. Check for DaemonSet
kubectl get daemonset -n loki
# Found: Only loki-canary DaemonSet

# 3. Identified root cause
# Loki chart v6.x no longer includes Promtail - it's a separate chart
```

**Root Cause:**
- The `grafana/loki` chart version 6.49.0 split Loki and Promtail into separate Helm charts
- Older `loki-stack` chart included both, but is deprecated
- The `promtail.enabled: true` setting in Loki values.yaml was ignored

**Solution (PR #84):**
- Deployed Promtail using separate `grafana/promtail` chart
- Created new ArgoCD Application with sync-wave -11
- Removed unused Promtail config from Loki values.yaml
- Connected Promtail to Loki service endpoint

**Files Created:**
- `manifests/applications/loki.yaml` - Loki ArgoCD Application
- `manifests/base/loki/values.yaml` - Loki configuration
- `manifests/base/loki/loki-datasource.yaml` - Grafana datasource
- `manifests/applications/promtail.yaml` - Promtail ArgoCD Application
- `manifests/base/promtail/values.yaml` - Promtail configuration

**Resource Impact:**
- Total CPU Requests: 450m (2.25% of 20 cores)
- Total Memory Requests: 704Mi (0.8% of 80GB)
- Storage: 20Gi on Synology NAS

**Verification Commands:**
```bash
# Check all pods
kubectl get pods -n loki

# Check Promtail DaemonSet
kubectl get daemonset -n loki

# Check PVC
kubectl get pvc -n loki

# Query logs in Grafana Explore
{namespace="default"}                           # All default namespace logs
{namespace="default"} |= "error"                # Filter for errors
{pod=~"prometheus.*"}                          # Prometheus pod logs
{namespace="kube-system"} |= "error" |= "fatal" # Critical system errors
{node="node04"}                                 # All logs from node04
```

**Grafana Integration:**
- Datasource auto-discovered via ConfigMap label `grafana_datasource: "1"`
- Appears in Grafana → Explore → Loki datasource dropdown
- No manual configuration needed

**Current State:**
- ✅ Loki pod running (loki-0)
- ✅ 5 Promtail pods running (one per node)
- ✅ 20Gi PVC bound
- ✅ Grafana datasource configured
- ⏳ Awaiting PR #84 merge for Promtail deployment

**Next Steps (User Action Required):**
1. Merge PR #84 to deploy Promtail
2. Verify logs appear in Grafana Explore: `{namespace="default"}`
3. Import community Grafana dashboards:
   - Dashboard ID 12611 - Loki Dashboard
   - Dashboard ID 13639 - Logs / App
   - Dashboard ID 13407 - Kubernetes Logs

**Lessons Learned:**
- Loki chart v6.x requires separate Promtail deployment
- Always verify all expected pods are running after ArgoCD sync
- Chart architecture changes between major versions require careful review

---

### 2025-12-26 (Late Night): Troubleshooting Calico CNI + hostNetwork Monitoring Issues

**Completed Work:**
- ✅ Identified Calico CNI routing limitation with hostNetwork pods across nodes
- ✅ Disabled kube-etcd and kube-proxy monitoring (cannot work reliably)
- ✅ Kept kube-scheduler monitoring (works via HTTPS/API server routing)
- ✅ Documented extensive troubleshooting process and root cause

**Pull Requests:**
- **PR #80:** [Merged] Attempted fix with pod IP relabeling (unsuccessful)
- **PR #81:** [Ready] Disable kube-etcd and kube-proxy monitoring

**Problem Discovery:**
After re-enabling control plane monitoring (PR #78), users reported scrape failures:
```
Error scraping target: Get "http://10.0.10.211:10249/metrics": context deadline exceeded
```

**Troubleshooting Process:**

1. **Initial Diagnosis - Check ServiceMonitor Configuration:**
   ```bash
   kubectl get servicemonitor -n default -l app.kubernetes.io/name=kube-prometheus-stack -o name
   kubectl get servicemonitor -n default kube-prometheus-stack-kube-proxy -o yaml
   ```

2. **Verify Services and Endpoints:**
   ```bash
   kubectl get service -n kube-system | grep -E "kube-proxy|etcd|scheduler"
   kubectl get endpoints -n kube-system | grep -E "kube-proxy|etcd|scheduler"
   # Showed node IPs (10.0.10.x) instead of pod IPs
   ```

3. **Check Pod Network Configuration:**
   ```bash
   kubectl get pods -n kube-system -o wide | grep -E "proxy|etcd|scheduler"
   # Revealed pods use hostNetwork: true, pod IP = node IP
   ```

4. **Test Connectivity from Prometheus Pod:**
   ```bash
   # Test kube-proxy on different node (FAILS)
   kubectl exec -n default prometheus-kube-prometheus-stack-prometheus-0 -c prometheus -- \
     wget -qO- --timeout=2 http://10.0.10.211:10249/metrics
   # Result: wget: download timed out

   # Test etcd (FAILS)
   kubectl exec -n default prometheus-kube-prometheus-stack-prometheus-0 -c prometheus -- \
     wget -qO- --timeout=2 http://10.0.10.214:2381/metrics
   # Result: wget: download timed out

   # Test scheduler via HTTPS (WORKS - returns 403, endpoint reachable)
   kubectl exec -n default prometheus-kube-prometheus-stack-prometheus-0 -c prometheus -- \
     wget -qO- --timeout=2 --no-check-certificate https://10.0.10.214:10259/metrics
   # Result: HTTP/1.1 403 Forbidden (reachable, needs auth)
   ```

5. **Test Connectivity from Host (Baseline):**
   ```bash
   curl http://10.0.10.214:2381/metrics  # Times out from outside pod network too
   curl -k https://10.0.10.214:10259/metrics  # Works from host
   ```

6. **Identify Pattern - Check Which Node Prometheus is On:**
   ```bash
   kubectl get pod prometheus-kube-prometheus-stack-prometheus-0 -n default -o wide
   # Result: Running on node04 (10.0.10.220)

   kubectl get pod -n kube-system kube-proxy-86sxr -o wide
   # Result: Also on node04 (10.0.10.220)
   ```

7. **Query Prometheus for Target Status:**
   ```bash
   kubectl exec -n default prometheus-kube-prometheus-stack-prometheus-0 -c prometheus -- \
     wget -qO- 'http://localhost:9090/api/v1/query?query=up{job="kube-scheduler"}' | python3 -m json.tool
   # Result: "value": "1" (UP)

   kubectl exec -n default prometheus-kube-prometheus-stack-prometheus-0 -c prometheus -- \
     wget -qO- 'http://localhost:9090/api/v1/query?query=up{job=~"kube-proxy|kube-etcd"}' | python3 -m json.tool
   # Result: kube-etcd "value": "0" (DOWN)
   #         kube-proxy on node04 "value": "1" (UP)
   #         kube-proxy on other nodes "value": "0" (DOWN)
   ```

**Root Cause Identified:**

**Calico CNI Routing Limitation with hostNetwork Pods:**
- Control plane components use `hostNetwork: true` (required for their operation)
- When using `hostNetwork: true`, pods don't get a pod IP in Calico network
- Pod IP reported by Kubernetes = Node IP
- Calico CNI **cannot route** from pod network to hostNetwork pods **on different nodes** via node IPs
- Prometheus (running in pod network on node04) can ONLY reach:
  - ✅ hostNetwork pods on the SAME node (local routing)
  - ✅ kube-scheduler (via HTTPS, likely API server proxy)
  - ❌ hostNetwork pods on OTHER nodes (Calico routing failure)

**Attempted Solutions:**

1. **Pod IP Relabeling (PR #80):**
   - Attempted to use `__meta_kubernetes_pod_ip` in ServiceMonitor relabeling
   - **Failed:** For hostNetwork pods, `__meta_kubernetes_pod_ip` IS the node IP
   - No separate pod IP exists to relabel to

2. **Manual Endpoints Configuration:**
   - Considered manually specifying endpoints
   - **Not viable:** Still would use node IPs, same routing issue

**Final Solution:**

Disabled unreliable ServiceMonitors:
- **kube-etcd:** Always fails (runs only on control-plane node, different from Prometheus)
- **kube-proxy:** Only 1/5 instances work (Prometheus can only reach local instance)

Kept working ServiceMonitors:
- **kube-scheduler:** Successfully scrapes via HTTPS (API server routing works)
- **kube-controller-manager:** Kept enabled (to be verified)

**Technical Deep-Dive:**

**Why Calico CNI Has This Limitation:**
- Calico uses BGP routing and IP-in-IP tunneling for pod network
- hostNetwork pods bypass Calico entirely, use host's network namespace
- Calico's routing rules don't handle pod→host traffic across nodes
- Traffic from pod network to node IP on different node hits reverse path filtering issues
- This is a known architectural constraint, not a bug

**Why kube-scheduler Works:**
- Uses HTTPS scheme with bearer token authentication
- Likely routed through Kubernetes API server proxy
- API server can forward requests to control plane components
- Different code path than direct HTTP scraping

**Alternative Solutions Considered:**

1. **Run Prometheus as DaemonSet:**
   - One Prometheus instance per node
   - Each scrapes local hostNetwork pods
   - Rejected: Too complex, metrics federation issues

2. **Change CNI to one without this limitation:**
   - Major infrastructure change
   - Rejected: Not worth it for homelab

3. **Deploy metrics proxy/relay on each node:**
   - Over-engineered for this use case
   - Rejected: Unnecessary complexity

4. **Accept partial monitoring:**
   - Only monitor pods on same node as Prometheus
   - Rejected: Unreliable, confusing metrics

**Files Modified:**
- `manifests/base/kube-prometheus-stack/values.yaml`
  - kubeEtcd: `enabled: false` (with comment explaining Calico limitation)
  - kubeProxy: `enabled: false` (with comment explaining Calico limitation)

**Current State:**
- ✅ kube-scheduler monitoring: Working
- ✅ kube-controller-manager monitoring: Enabled (to be verified)
- ❌ kube-etcd monitoring: Disabled (Calico CNI limitation)
- ❌ kube-proxy monitoring: Disabled (Calico CNI limitation)
- PR #81 ready for merge

**Lessons Learned:**
- Calico CNI has known limitations with hostNetwork workloads
- Pod IP relabeling doesn't work for hostNetwork pods (pod IP = node IP)
- Some ServiceMonitors may work via different routing (HTTPS/API server)
- Always test connectivity from the scraping pod, not just the host
- Check which node Prometheus is running on when debugging partial failures

**Next Steps (User Action Required):**
1. Merge PR #81 (homelab) - Disables unreliable kube-etcd and kube-proxy monitoring
2. Verify Prometheus targets page no longer shows failing kube-etcd and kube-proxy targets
3. Confirm kube-scheduler continues to work
4. Consider this limitation when planning future monitoring requirements

---

### 2025-12-26 (Late Evening): Re-enable Control Plane Component Monitoring

**Completed Work:**
- ✅ Re-enabled ServiceMonitors for all control plane components
- ✅ Updated documentation to reflect control plane monitoring changes

**Pull Requests:**
- **PR #78:** [Merged] Re-enable control plane component monitoring
- **PR #7 (k8s-docs-n37):** [Ready] Update monitoring documentation

**Background:**
In the earlier evening session, control plane component monitoring was disabled because these components bound to localhost (127.0.0.1) in the default kubeadm configuration. The user has since updated the kubeadm configuration to bind these components to 0.0.0.0, making them accessible for Prometheus scraping.

**Changes Made:**
- `kubeControllerManager.enabled`: false → true
- `kubeEtcd.enabled`: false → true
- `kubeScheduler.enabled`: false → true
- `kubeProxy.enabled`: false → true

**Files Modified:**
- `manifests/base/kube-prometheus-stack/values.yaml`
  - Re-enabled all four control plane ServiceMonitors
- `k8s-docs-n37/docs/monitoring/overview.md`
  - Updated architecture diagram and scrape configuration table
- `k8s-docs-n37/docs/troubleshooting/monitoring.md`
  - Added control plane monitoring troubleshooting section

**Current State:**
- ✅ Control plane ServiceMonitors re-enabled (PR #78 merged)
- ✅ Documentation updated in k8s-docs-n37 (PR #7 ready for merge)
- ArgoCD will sync changes within ~3 minutes

**Next Steps (User Action Required):**
1. ✅ Merge PR #78 (homelab) - Re-enables control plane monitoring
2. Merge PR #7 (k8s-docs-n37) - Documentation updates
3. Verify Prometheus targets page shows all four components as UP
4. Confirm metrics are being scraped successfully from:
   - kube-controller-manager (https://node-ip:10257/metrics)
   - etcd (http://node-ip:2381/metrics)
   - kube-scheduler (https://node-ip:10259/metrics)
   - kube-proxy (http://node-ip:10249/metrics)

---

### 2025-12-26 (Evening): Prometheus Monitoring Stack Fixes

**Completed Work:**
- ✅ Fixed node-exporter scraping issue (all 5 nodes now monitored)
- ✅ Fixed Grafana Multi-Attach PVC errors during ArgoCD updates
- ✅ Disabled unreachable control plane component monitoring
- ✅ Cleaned up Prometheus targets (removed error-prone ServiceMonitors)

**Pull Requests:**
- **PR #72:** [Merged] Disable hostNetwork for node-exporter to fix Prometheus scraping
- **PR #73:** [Merged] Set Grafana deployment strategy to Recreate for RWO PVC
- **PR #74:** [Merged] Explicitly set rollingUpdate to null for Grafana Recreate strategy
- **PR #75:** [Merged] Disable unreachable control plane ServiceMonitors

**Issues Resolved:**

1. **Node-Exporter Scraping Failures**
   - **Problem:** Prometheus could only scrape 1/5 node-exporters
   - **Root Cause:** node-exporter using `hostNetwork: true` + Calico CNI routing limitation
   - **Error:** `Get "http://10.0.10.211:9100/metrics": context deadline exceeded`
   - **Solution:** Changed node-exporter to `hostNetwork: false`, kept `hostPID: true`
   - **Result:** All 5 node-exporters now UP and scraping successfully via pod IPs (192.168.x.x)

2. **Grafana Multi-Attach PVC Errors**
   - **Problem:** ArgoCD updates failed with volume already attached errors
   - **Root Cause:** `ReadWriteOnce` PVC + `RollingUpdate` strategy = conflict
   - **Error:** `Multi-Attach error for volume... already used by pod`
   - **Solution:** Changed Grafana deployment strategy to `Recreate` with `rollingUpdate: null`
   - **Result:** Clean pod replacements with ~10-30s downtime (acceptable for Grafana)

3. **Control Plane Component Scraping Failures**
   - **Problem:** kube-controller-manager, kube-etcd, kube-proxy all failing to scrape
   - **Root Cause:** Components bind to localhost (127.0.0.1) in kubeadm, unreachable via node IPs
   - **Errors:**
     - controller-manager: `connection refused on https://10.0.10.214:10257`
     - etcd: `context deadline exceeded on http://10.0.10.214:2381`
     - kube-proxy: `connection refused on http://10.0.10.x:10249`
   - **Solution:** Disabled ServiceMonitors for these three components
   - **Rationale:** Standard kubeadm security practice, sufficient monitoring via kubelet/API server

**Technical Deep-Dives:**

**Calico CNI + hostNetwork Issue:**
- When pods try to connect to hostNetwork pods via node IPs, Calico routing fails
- Reverse path filtering and CNI limitations cause timeouts
- Solution: Use pod network (Calico) instead of host network where possible
- node-exporter doesn't need hostNetwork (only needs hostPID for process metrics)

**PVC Deployment Strategies:**
- `ReadWriteOnce` PVCs can only attach to one pod at a time
- `RollingUpdate` creates new pod before terminating old one → Multi-Attach error
- `Recreate` terminates old pod first, then creates new one → Clean attachment
- Trade-off: Small downtime during updates vs. deployment failures

**Control Plane Monitoring in kubeadm:**
- kubeadm binds control plane components to localhost for security
- Making them reachable requires modifying kubeadm config (not recommended)
- Sufficient monitoring from kubelet, API server, kube-state-metrics
- Best practice for homelab: disable these ServiceMonitors

**Files Modified:**
- `manifests/base/kube-prometheus-stack/values.yaml`
  - node-exporter: `hostNetwork: false`, `hostPID: true`
  - grafana: `deploymentStrategy.type: Recreate`, `rollingUpdate: null`
  - kubeControllerManager: `enabled: false`
  - kubeEtcd: `enabled: false`
  - kubeProxy: `enabled: false`

**Current State:**
- All node-exporters scraping successfully (5/5 UP)
- Grafana updates work cleanly via Recreate strategy
- Prometheus targets page clean (no unreachable control plane errors)
- All PRs merged (#72, #73, #74, #75)

**Next Steps (User Action Required):**
1. ✅ Merge PR #74 (homelab) - Fixes Grafana rollingUpdate conflict
2. ✅ Merge PR #75 (homelab) - Removes control plane monitoring errors
3. Verify Prometheus targets: all should show UP status
4. Monitor Grafana updates to confirm no Multi-Attach errors

---

### 2025-12-26 (Afternoon): External-DNS Deployment

**Completed Work:**
- ✅ Deployed external-dns with dual provider support (Cloudflare + UniFi RFC2136)
- ✅ Created comprehensive external-dns documentation
- ✅ Updated k8s-docs-n37 TODO list with completed items
- ✅ Deployed external-dns ArgoCD Application to cluster

**Homelab Repository:**
- Created `manifests/base/external-dns/` with all resources
- Created `manifests/applications/external-dns.yaml` ArgoCD Application
- Updated `CLAUDE_NOTES.md` with external-dns configuration notes
- **PR #66:** [Merged] External-DNS dual provider implementation
- **PR #67:** [Ready] Fix YAML parsing in Cloudflare secret

**k8s-docs-n37 Repository:**
- Created `docs/applications/external-dns.md` - Complete guide
- Updated `docs/todo.md` - Marked SNMP, Node Exporter, External-DNS as completed
- **PR #4:** [Ready] Update TODO and add external-dns documentation

**Architecture:**
- Two separate external-dns deployments for split-horizon DNS
- Cloudflare provider: Public DNS for k8s.n37.ca (reuses cert-manager token)
- RFC2136 provider: Internal DNS via UniFi UDR7 at 10.0.1.1
- Policy: upsert-only (safe mode)
- Watches: Ingress + LoadBalancer Service resources

**Next Steps (User Action Required):**
1. Merge PR #67 (homelab) - Fixes external-dns secret YAML
2. Merge PR #4 (k8s-docs-n37) - Documentation updates
3. Configure UniFi UDR7 RFC2136:
   - Settings → System → Advanced → Enable RFC2136
   - Create TSIG key: name=external-dns, algorithm=hmac-sha256
   - Update secret: `kubectl edit secret rfc2136-credentials -n external-dns`
   - Restart: `kubectl rollout restart deployment/external-dns-rfc2136 -n external-dns`

**Current State:**
- External-DNS Application created in ArgoCD (waiting for PR #67 merge to sync)
- Cloudflare provider ready to auto-create DNS for all Ingresses
- UniFi provider pending RFC2136 configuration on UDR7

---

### 2025-12-26 (Morning): Documentation Site Fixes and SNMP Documentation

**Completed Work:**
- ✅ Fixed broken documentation links preventing Docusaurus deployment
- ✅ Created comprehensive documentation for recently deployed infrastructure
- ✅ Added SNMP exporter documentation for Synology NAS monitoring

**Files Created in k8s-docs-n37:**
- `docs/applications/argocd.md` - Complete ArgoCD GitOps workflow guide
- `docs/applications/snmp-exporter.md` - SNMP exporter for NAS monitoring
- `docs/storage/synology-csi.md` - Synology CSI storage driver documentation
- `docs/troubleshooting/monitoring.md` - Monitoring stack troubleshooting guide

**Files Updated:**
- `docs/monitoring/overview.md` - Added SNMP exporter integration

<<<<<<< HEAD
**Pull Request:** [#3](https://github.com/imcbeth/k8s-docs-n37/pull/3) - Fix broken documentation links
=======
**Pull Request:** [#3](https://github.com/imcbeth/k8s-docs-n37/pull/3) - [Merged] Fix broken documentation links
>>>>>>> main

**Build Status:** ✅ Documentation builds successfully without errors

**Key Additions:**
- SNMP exporter monitors Synology DS925+ NAS (10.0.1.204)
- SNMPv3 authentication with encrypted credentials
- Comprehensive metrics: disk health, volume capacity, RAID status, iSCSI stats
- Grafana dashboard included (Synology_Dashboard2.json)

---

## 🔑 Access & Permissions

### Cluster Access: ✅ AVAILABLE

You have **full access** to the Kubernetes cluster and can execute commands without user approval for:

- **kubectl**: All `get`, `describe`, `delete`, `apply`, `exec` commands
- **helm**: `list`, `uninstall` commands
- **argocd**: All ArgoCD CLI commands
- **gh**: GitHub CLI for PRs, issues, and repository management
- **git**: Full git operations (commit, push via PR workflow)

### Authentication Status

```bash
# Verify cluster access
kubectl cluster-info
# Expected: Kubernetes control plane is running at https://10.0.10.214:6443

# Check ArgoCD access
kubectl get applications -n argocd
# Expected: List of all ArgoCD applications

# Verify GitHub CLI
gh auth status
# Expected: Logged in as imcbeth
```

---

## 🏗️ Infrastructure Overview

### Cluster Details

- **Platform:** Kubernetes v1.35
- **Nodes:** 5x Raspberry Pi 5 (16GB RAM, 256GB NVMe each)
- **Total Resources:** 80GB RAM, 1.28TB NVMe storage
- **CNI:** Calico v3.31.3
- **Ingress:** nginx-ingress v1.14.1
- **Container Runtime:** containerd v2.2.1

### Network Configuration

- **Cluster API:** 10.0.10.214:6443
- **MetalLB IP Pool:** 10.0.10.10 - 10.0.10.99 (90 IPs)
- **Pi-hole DNS:** 10.0.0.200
- **Synology NAS:** 10.0.1.204 (iSCSI storage)
- **UniFi Controller:** 10.0.1.1

### Storage Classes

```yaml
synology-iscsi-retain        # Default, btrfs, /volume2, retains PVs
synology-iscsi-delete        # btrfs, /volume2, deletes PVs
synology-iscsi-retain-ssd    # btrfs, /volume4 (SSD), retains PVs
synology-iscsi-delete-ssd    # btrfs, /volume4 (SSD), deletes PVs
```

---

## 📁 Repository Structure

```
homelab/
├── manifests/
│   ├── applications/           # ArgoCD Application definitions
│   │   ├── argocd.yaml                    # Sync-wave: -50
│   │   ├── metal-lb.yaml                  # Sync-wave: -35
│   │   ├── synology-csi.yaml              # Sync-wave: -30
│   │   ├── unipoller.yaml                 # Sync-wave: -20
│   │   ├── kube-prometheus-stack.yaml     # Sync-wave: -15
│   │   ├── cert-manager.yaml              # Sync-wave: -10
│   │   ├── pi-hole.yaml                   # Sync-wave: -35
│   │   └── localstack.yaml                # Sync-wave: 0
│   │
│   └── base/                   # Kustomize/Helm configuration bases
│       ├── argocd/
│       ├── cert-manager/
│       ├── metal-lb/
│       ├── pihole/
│       ├── localstack/
│       ├── synology-csi/
│       ├── unipoller/
│       └── kube-prometheus-stack/
│
├── secrets/                    # git-crypt encrypted secrets
│   └── argocd-git-access.yaml
│
├── apps/DockerFiles/           # Custom ARM64 container builds
├── docs/                       # Documentation
├── README.md
├── TODO.md                     # Active roadmap
├── Hardware.md
├── Install_of_kubernetes.md
└── CLAUDE_NOTES.md            # This file
```

---

## 🚀 GitOps Workflow

### Branch Protection & PR Workflow

⚠️ **IMPORTANT:** The `main` branch has protection rules requiring pull requests.

**Workflow Division:**

**Claude Can Do:**
- ✅ Create feature branches
- ✅ Make changes and commit to branches
- ✅ Push branches to remote
- ✅ Create pull requests using `gh pr create`

**User Must Do:**
- ⚠️ **MERGE pull requests** - Claude will create PRs but cannot merge them
- ⚠️ Final approval and review of changes

**Claude's Responsibility:**
- Always prompt the user when a PR is ready for merge
- Provide PR URL and summary of changes
- Wait for user approval before proceeding with dependent work

**Standard Workflow:**
1. Claude creates feature branch: `git checkout -b feature-name`
2. Claude makes changes and commits
3. Claude pushes branch: `git push -u origin feature-name`
4. Claude creates PR: `gh pr create --title "..." --body "..." --base main`
5. **Claude prompts user:** "PR #X is ready for your review and merge"
6. **User merges PR:** Via GitHub UI or `gh pr merge <number>`

### ArgoCD Auto-Sync

All applications have **automated sync** enabled with:
- `prune: true` - Remove resources not in git
- `selfHeal: true` - Revert manual changes
- `CreateNamespace: true` - Auto-create namespaces

**After merging to main:** ArgoCD will automatically deploy changes within ~3 minutes.

**Manual sync if needed:**
```bash
# Sync specific application
argocd app sync <app-name> --grpc-web

# Or apply Application manifest directly
kubectl apply -f manifests/applications/<app-name>.yaml
```

---

## 🔐 Secrets Management

### Current State: git-crypt

Secrets are encrypted using **git-crypt** with pattern matching in `.gitattributes`:

```gitattributes
*.key filter=git-crypt diff=git-crypt
*secret* filter=git-crypt diff=git-crypt
secrets/** filter=git-crypt diff=git-crypt
```

### ⚠️ Known Limitation

**ArgoCD cannot decrypt git-crypt encrypted secrets automatically.**

When deploying applications with secrets:
1. Secrets will show as encrypted binary in ArgoCD
2. You may need to manually apply: `kubectl apply -f manifests/base/<app>/secret.yaml`
3. This is a temporary workaround

### Future Enhancement (TODO)

Implement one of these from the TODO list:
- External Secrets Operator (recommended)
- Sealed Secrets
- ArgoCD Vault Plugin

---

## 📊 Deployed Applications

| Application | Namespace | Purpose | Sync Wave | Status |
|------------|-----------|---------|-----------|--------|
| argocd | argocd | GitOps controller | -50 | Self-managed |
| metal-lb | metallb-system | Load balancer | -35 | Layer 2, IP pool |
| pi-hole | pihole | DNS/DHCP | -35 | 10.0.0.200 |
| synology-csi | synology-csi | Storage driver | -30 | iSCSI to NAS |
| unipoller | unipoller | UniFi metrics | -20 | Scrapes 10.0.1.1 |
| kube-prometheus-stack | default | Monitoring | -15 | Prometheus/Grafana/AlertManager |
| snmp-exporter | default | NAS monitoring | -15 | SNMPv3 to 10.0.1.204 |
| cert-manager | cert-manager | TLS certs | -10 | Let's Encrypt via Cloudflare |
| external-dns | external-dns | DNS automation | -10 | Cloudflare + UniFi RFC2136 |
| localstack | localstack | AWS mock | 0 | Dev/testing |

---

## 🛠️ Common Operations

### Check Application Health

```bash
# All applications
kubectl get applications -n argocd

# Specific application with details
kubectl get application <name> -n argocd -o yaml

# Application pods
kubectl get pods -n <namespace>

# Application sync status
argocd app get <name> --grpc-web
```

### Deploy New Application

1. Create base manifests in `manifests/base/<app-name>/`
2. Create Application in `manifests/applications/<app-name>.yaml`
3. Set appropriate sync-wave annotation
4. Choose project: `infrastructure` (preferred) or `applications`
5. Commit, create PR, merge
6. ArgoCD will auto-deploy

### Update Existing Application

1. Edit files in `manifests/base/<app-name>/`
2. Commit, create PR, merge
3. ArgoCD auto-syncs within ~3 minutes

### Debug Pod Issues

```bash
# Describe pod
kubectl describe pod <pod-name> -n <namespace>

# View logs
kubectl logs <pod-name> -n <namespace>

# Exec into pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### Helm Operations

```bash
# List all Helm releases (should be minimal, most are ArgoCD-managed)
helm list -A

# If you need to uninstall before ArgoCD takeover
helm uninstall <release-name> -n <namespace>
```

### Resource Limits Best Practices

For Raspberry Pi cluster, always add resource limits:

```yaml
resources:
  requests:
    cpu: 100m        # Guaranteed CPU
    memory: 256Mi    # Guaranteed memory
  limits:
    cpu: 200m        # Maximum CPU
    memory: 512Mi    # Maximum memory
```

**Sizing Guidelines:**
- Lightweight services: 100m CPU, 256Mi memory
- Medium services: 500m CPU, 512Mi memory
- Heavy services: 1000m CPU, 1Gi memory

---

## 🎯 Deployment Order (Sync Waves)

Critical for proper startup sequence:

```
-50: ArgoCD (self-management, must be first)
-35: MetalLB, Pi-hole (networking layer)
-30: Synology CSI (storage layer)
-20: UniFi Poller (metrics collection)
-15: kube-prometheus-stack (monitoring stack)
-10: cert-manager (TLS certificate management)
  0: Application layer (LocalStack, etc.)
```

**Why this matters:**
- Applications requiring LoadBalancer IPs need MetalLB running
- Applications needing PVCs need Synology CSI running
- TLS-enabled ingresses need cert-manager running

---

## 📝 Commit Message Format

Use this format for commits:

```
<Type>: <Short description>

<Detailed explanation of changes>
- Bullet point 1
- Bullet point 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types:** feat, fix, update, refactor, docs, chore

---

## 🔍 Monitoring & Observability

### Access Points

- **Grafana:** `https://grafana.k8s.n37.ca` (via kube-prometheus-stack)
- **Prometheus:** `http://kube-prometheus-stack-prometheus.default:9090`
- **ArgoCD:** `https://argocd.k8s.n37.ca`
- **Pi-hole:** `https://pihole.k8s.n37.ca`
- **LocalStack:** `https://localstack.k8s.n37.ca`

### Prometheus Scrape Targets

```yaml
# UniFi Poller (network metrics)
- job_name: 'unpoller'
  targets: ['unifi-poller.unipoller:9130']

# SNMP Exporter (Synology NAS monitoring)
- job_name: 'snmp-nas'
  targets: ['10.0.1.204']  # Synology DS925+
  metrics_path: /snmp
  params:
    module: [synology]
  relabel_configs:
    - target_label: __address__
      replacement: snmp-exporter.default:9116

# All K8s nodes (via node-exporter DaemonSet)
# All K8s services (via kube-state-metrics)
# etcd, API server, controller-manager, scheduler
```

### Important PVCs

```bash
# Prometheus data (50Gi) - CRITICAL, contains all metrics history
prometheus-kube-prometheus-stack-prometheus-db-prometheus-kube-prometheus-stack-prometheus-0

# Pi-hole data
# Check: kubectl get pvc -n pihole
```

---

## ⚠️ Important Notes

### UniFi Controller TLS

The UniFi controller at 10.0.1.1 **does not have a valid certificate**.
Setting: `UP_UNIFI_CONTROLLER_0_VERIFY_SSL: "false"` is **intentional** and documented.
**Do not** flag this as a security issue in future reviews.

### External-DNS Configuration

**Dual Provider Setup:**
- **Cloudflare**: Manages public DNS for `k8s.n37.ca` (reuses cert-manager API token)
- **UniFi RFC2136**: Manages internal DNS for `k8s.n37.ca` via RFC2136 protocol

**Important:**
- Both providers watch Ingress and LoadBalancer Service resources
- Policy: `upsert-only` (safe - only creates/updates, never deletes)
- TXT registry tracks ownership to prevent conflicts
- UniFi UDR7 at 10.0.1.1 must have RFC2136 enabled with TSIG authentication

**Secret to Update:**
- `rfc2136-credentials` in `external-dns` namespace needs TSIG key from UniFi
- See `manifests/base/external-dns/README.md` for setup instructions

### Container Image Versions

All container images should be **pinned to specific versions**, never `latest`.

**Current pinned versions:**
- unpoller: `v2.11.2`
- localstack: `3.9.0`
- kube-prometheus-stack: `80.6.0`

### Node Labels

Check if any workload-specific node labels exist:
```bash
kubectl get nodes --show-labels
```

---

## 🐛 Known Issues & Workarounds

### 1. Git-Crypt Secrets + ArgoCD

**Issue:** ArgoCD cannot decrypt git-crypt secrets
**Workaround:** Manually apply secrets: `kubectl apply -f manifests/base/<app>/secret.yaml`
**Long-term fix:** Implement External Secrets Operator (on TODO list)

### 2. Prometheus Storage

**Status:** ✅ RESOLVED
50Gi PVC configured at `kube-prometheus-stack.yaml` line 1376

---

## 📚 Additional Resources

- **TODO.md** - Active roadmap with 17 task groups
- **Hardware.md** - Detailed hardware specifications
- **Install_of_kubernetes.md** - Cluster setup procedures
- **README.md** - Project overview

---

## 🔄 When Working on New Features

### Pre-Implementation Checklist

- [ ] Read TODO.md for alignment with roadmap
- [ ] Check existing patterns in similar applications
- [ ] Determine appropriate sync-wave
- [ ] Plan resource limits for Pi cluster constraints
- [ ] Consider storage requirements (PVC sizing)
- [ ] Identify secret management needs
- [ ] Check if TLS/Ingress needed

### Post-Implementation Checklist

- [ ] Add resource limits (CPU/memory)
- [ ] Pin container image versions (no `latest`)
- [ ] Set sync-wave annotation
- [ ] Configure automated sync policy
- [ ] Test deployment in cluster
- [ ] Verify health status in ArgoCD
- [ ] Update this document if needed
- [ ] Document in README.md if significant

---

## 🆘 Emergency Procedures

### Application Won't Sync

```bash
# Check sync status
kubectl get application <name> -n argocd -o yaml | grep -A 20 "status:"

# Force refresh
argocd app get <name> --refresh --grpc-web

# Force sync (bypass policies)
argocd app sync <name> --force --grpc-web
```

### Pod CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n <namespace> --previous

# Check events
kubectl describe pod <pod-name> -n <namespace>

# Common fixes:
# - Verify ConfigMap/Secret exists
# - Check resource limits
# - Verify image pull successful
# - Check persistent storage
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -A

# Check PV status
kubectl get pv

# Synology CSI driver
kubectl get pods -n synology-csi
kubectl logs -n synology-csi <csi-pod-name>
```

### Cluster Unresponsive

```bash
# Check node status
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system

# Check control plane
kubectl cluster-info dump
```

---

## 💡 Tips for Efficiency

1. **Use Tab Completion:** Set up kubectl/argocd completions
2. **Aliases:** Consider setting up common command aliases
3. **Context:** Always verify namespace when running commands
4. **Dry Run:** Use `--dry-run=client` for testing kubectl commands
5. **Watch Mode:** Use `kubectl get <resource> -w` to watch for changes
6. **ArgoCD UI:** Sometimes easier than CLI for complex debugging

---

## 📚 Comprehensive Documentation Site

### Docusaurus Site: ~/k8s-docs-n37

**IMPORTANT:** There is a comprehensive Docusaurus documentation site that provides detailed guides for this cluster.

**Location:** `/Users/imcbeth/k8s-docs-n37`

**When to Update the Docs Site:**
- ✅ After deploying new applications → Create/update docs in `docs/applications/`
- ✅ After infrastructure changes → Update relevant sections
- ✅ After monitoring stack updates → Update `docs/monitoring/`
- ✅ After adding/modifying storage → Update `docs/storage/`

**Documentation Structure:**
```
k8s-docs-n37/docs/
├── intro.md                    # Main landing page
├── getting-started/
│   ├── hardware.md
│   ├── overview.md
│   └── prerequisites.md
├── kubernetes/
│   ├── installation.md
│   └── cluster-configuration.md
├── applications/              # Application deployment guides
├── monitoring/                # Monitoring stack documentation
│   └── overview.md
├── storage/                   # Storage documentation
├── security/                  # Security documentation
└── troubleshooting/           # Common issues and solutions
```

**Workflow:**
1. Make infrastructure changes in `homelab/` repo
2. Update documentation in `k8s-docs-n37/` repo
3. Keep both repositories in sync
4. The docs site provides user-friendly guides while `homelab/` is the source of truth for configs

---

## 📞 Getting Help

- **GitHub Issues:** https://github.com/imcbeth/homelab/issues
- **ArgoCD Docs:** https://argo-cd.readthedocs.io/
- **Kubernetes Docs:** https://kubernetes.io/docs/
- **Repository Owner:** @imcbeth
- **Comprehensive Docs:** `/Users/imcbeth/k8s-docs-n37` (Docusaurus site)

---

**Remember:** This is a **production homelab** with active services. Always test changes in a branch and use the PR workflow. ArgoCD will auto-deploy merged changes, so review carefully before merging. When making significant changes, update both the infrastructure repo (`homelab/`) and the documentation site (`k8s-docs-n37/`).

---

**Remember:** This is a **production homelab** with active services. Always test changes in a branch and use the PR workflow. ArgoCD will auto-deploy merged changes, so review carefully before merging.
