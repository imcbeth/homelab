# 2025-12-26 (Late Night): Troubleshooting Calico CNI + hostNetwork Monitoring Issues

**Completed Work:**
- Identified Calico CNI routing limitation with hostNetwork pods across nodes
- Disabled kube-etcd and kube-proxy monitoring (cannot work reliably)
- Kept kube-scheduler monitoring (works via HTTPS/API server routing)

**Pull Requests:**
- **PR #81:** [Ready] Disable kube-etcd and kube-proxy monitoring

**Root Cause: Calico CNI Routing Limitation**

Control plane components use `hostNetwork: true`. When pods try to connect to hostNetwork pods via node IPs, Calico routing fails:
- Pod IP = Node IP for hostNetwork pods
- Calico cannot route from pod network to hostNetwork pods on different nodes
- Prometheus can ONLY reach hostNetwork pods on the SAME node

**Why kube-scheduler Works:**
Uses HTTPS with bearer token authentication, likely routed through Kubernetes API server proxy (different code path than direct HTTP scraping).

**Final Solution:**

Disabled unreliable ServiceMonitors:
- **kube-etcd:** Always fails (runs only on control-plane, different from Prometheus)
- **kube-proxy:** Only 1/5 instances work (Prometheus can only reach local instance)

Kept working:
- **kube-scheduler:** Successfully scrapes via HTTPS

**Technical Details:**
- Calico uses BGP routing and IP-in-IP tunneling for pod network
- hostNetwork pods bypass Calico entirely, use host's network namespace
- Traffic from pod network to node IP on different node hits reverse path filtering issues

**Files Modified:**
- `manifests/base/kube-prometheus-stack/values.yaml`
  - kubeEtcd: `enabled: false`
  - kubeProxy: `enabled: false`
