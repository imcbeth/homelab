# Cluster Health Report - 2026-02-15

## Cluster Overview
- **Nodes**: 5 (1 control-plane + 4 workers), all healthy
- **ArgoCD Apps**: 25/25 Synced + Healthy
- **Pods**: All Running (no CrashLoopBackOff or Pending)
- **Node Resources**: CPU 3-15%, Memory 15-31% — well within limits

---

## CRITICAL: 5 Prometheus Targets Down (TargetDown alerts firing)

All failures are `context deadline exceeded` — caused by NetworkPolicy gaps in `manifests/base/network-policies/default/network-policy.yaml`.

### Issue 1: Kubelet metrics (all 5 nodes, 15 scrape endpoints down)
- **Targets**: `https://10.0.10.x:10250/metrics`, `/metrics/cadvisor`, `/metrics/probes`
- **Root cause**: Kubelet runs on the host network (node IPs 10.0.10.x), not as a pod. The egress rule uses `namespaceSelector: {}` which only matches pod IPs. Need `ipBlock: cidr: 10.0.10.0/24` for port 10250.
- **Impact**: No container CPU/memory metrics (cadvisor), no kubelet health metrics, no probe metrics.

### Issue 2: kube-controller-manager (1 target down)
- **Target**: `https://10.0.10.214:10257/metrics`
- **Root cause**: Same as kubelet — static pod on host network. Need `ipBlock` rule for port 10257.

### Issue 3: kube-scheduler (1 target down)
- **Target**: `https://10.0.10.214:10259/metrics`
- **Root cause**: Same — static pod on host network. Need `ipBlock` rule for port 10259.

### Issue 4: CoreDNS metrics (2 targets down)
- **Targets**: `http://192.168.235.x:9153/metrics`
- **Root cause**: Port 9153 is **missing** from the egress port list in the default namespace policy. CoreDNS runs as a pod (pod IP), so `namespaceSelector: {}` would match, but port 9153 is not enumerated.

### Issue 5: Velero metrics (1 target down)
- **Target**: `http://192.168.196.149:8085/metrics`
- **Root cause**: Port 8085 is **missing** from the egress port list. The velero-network-policy correctly allows ingress from default:8085, but default's egress doesn't include 8085.

### Fix (default/network-policy.yaml)

Add to the `ipBlock: 10.0.10.0/24` egress rule (currently only has port 6443):
```yaml
    - to:
        - ipBlock:
            cidr: 10.0.10.0/24
      ports:
        - protocol: TCP
          port: 6443
        - protocol: TCP
          port: 10250  # kubelet
        - protocol: TCP
          port: 10257  # kube-controller-manager
        - protocol: TCP
          port: 10259  # kube-scheduler
```

Add to the `namespaceSelector: {}` egress port list:
```yaml
        - protocol: TCP
          port: 9153   # CoreDNS metrics
        - protocol: TCP
          port: 8085   # Velero metrics
```

---

## HIGH: 2 ServiceMonitors Not Discovered by Prometheus

The Prometheus operator requires label `release: kube-prometheus-stack` on all ServiceMonitors/PodMonitors. These two are missing it:

### 1. `ingress-nginx/ingress-nginx-controller`
- **File**: `manifests/base/ingress-nginx/values.yaml`
- **Fix**: Add `additionalLabels` to the serviceMonitor config:
```yaml
  metrics:
    serviceMonitor:
      enabled: true
      additionalLabels:
        release: kube-prometheus-stack
```

### 2. `falco/falco-falcosidekick`
- **File**: `manifests/base/falco/values.yaml`
- **Fix**: Add the label via the falcosidekick serviceMonitor config in Helm values.

---

## HIGH: Missing ServiceMonitors (metrics not collected)

These services expose Prometheus metrics but have no ServiceMonitor:

| Service | Namespace | Metrics Port | Fix |
|---------|-----------|-------------|-----|
| cert-manager | cert-manager | 9402 (`tcp-prometheus-servicemonitor`) | Enable `prometheus.servicemonitor.enabled` in Helm values |
| cert-manager-cainjector | cert-manager | 8080 (`http-metrics`) | Same Helm values |
| cert-manager-webhook | cert-manager | 9402 (`metrics`) | Same Helm values |
| calico-kube-controllers-metrics | calico-system | `metrics-port` | Create ServiceMonitor manually (not in Helm chart) |
| ArgoCD (all components) | argocd | 8083 (metrics) | Enable `controller.metrics.serviceMonitor.enabled` etc. in argocd-config.yaml |

---

## HIGH: ArgoCD Application Controller OOMKilled (13 restarts in 46h)

- **Pod**: `argocd-application-controller-0` on node01
- **Current limit**: 1Gi memory
- **Last termination**: OOMKilled (exit 137) at 12:00 on Feb 15
- **File**: `manifests/base/argocd/argocd-config.yaml` line 24
- **Fix**: Increase memory limit to 1.5Gi or 2Gi. With 25 apps (including large ones like tigera-operator, kube-prometheus-stack), 1Gi is too tight.

---

## MEDIUM: cert-manager startupapicheck Job Blocked by Gatekeeper

- **Event**: `FailedCreate` — "admission webhook validation.gatekeeper.sh denied the request: Container cert-manager-startupapicheck does not have CPU/memory limits"
- **Impact**: PostSync hook job cannot create pods. Non-critical (cert-manager itself works) but creates continuous warning events (271 failures in 4h28m).
- **Fix**: Add resource limits to cert-manager Helm values:
```yaml
startupapicheck:
  resources:
    requests:
      cpu: 10m
      memory: 32Mi
    limits:
      cpu: 50m
      memory: 64Mi
```

---

## MEDIUM: Firing Prometheus Alerts Summary

| Alert | Severity | Count | Notes |
|-------|----------|-------|-------|
| TargetDown | warning | 5 | See Critical section above |
| CriticalVulnerabilitiesDetected | warning | 58 | Trivy-found CVEs in container images. Review and plan upgrades. |
| ExposedSecretsDetected | critical | 1 | localstack pod — expected for dev tool, consider suppressing |
| HighRiskRBACPermissions | warning | 42 | Trivy RBAC assessment — most are third-party operators (tigera, istiod, cert-manager) with inherently broad permissions |
| CriticalClusterRoleRBACIssues | warning | 1 | 55 ClusterRoles flagged — review for overly permissive roles |
| HighClusterRoleRBACIssues | info | 1 | 19 ClusterRoles with HIGH severity — informational |
| CISKubernetesBenchmarkFailures | info | 1 | CIS compliance gaps — review trivy reports |
| NSAKubernetesHardeningFailures | info | 1 | NSA hardening gaps — review trivy reports |
| HighVulnerabilityCount | info | 1 | General cluster vuln count alert |
| Watchdog | none | 1 | Expected — confirms Alertmanager is working |

---

## LOW: Intermittent Probe Failures (Events)

These are transient and non-recurring:
- **istio-cni-node-6zzhb**: Readiness probe 503 (node04) — single event, now healthy
- **loki-canary-v4664**: Readiness probe timeout (node03) — single event, now healthy
- **metallb-speaker-l9nct**: Liveness probe timeout (control-plane) — single event, now healthy

---

## LOW: external-dns-cloudflare Restarts

- **Pod**: `external-dns-cloudflare-5fbbcbdc87-x287c` — 15 restarts in 21d
- Currently healthy, logs show normal operation. Likely intermittent Cloudflare API timeouts.

---

## Velero Backups: Healthy

- Storage location: `default` (Available)
- 3 schedules running on time:
  - `velero-daily-argocd`: Last backup 22h ago
  - `velero-daily-critical-pvcs`: Last backup 21h ago
  - `velero-weekly-cluster-resources`: Last backup 20h ago

---

## Summary: Prioritized Fix List

1. **[CRITICAL]** Fix NetworkPolicy egress for kubelet/scheduler/controller-manager/CoreDNS/Velero scraping
2. **[HIGH]** Add `release: kube-prometheus-stack` label to ingress-nginx and falco ServiceMonitors
3. **[HIGH]** Add ServiceMonitors for cert-manager, calico-kube-controllers, ArgoCD
4. **[HIGH]** Increase ArgoCD application-controller memory limit (1Gi → 1.5-2Gi)
5. **[MEDIUM]** Add resource limits to cert-manager startupapicheck job
6. **[LOW]** Review Trivy vulnerability reports for critical CVEs and plan image upgrades
