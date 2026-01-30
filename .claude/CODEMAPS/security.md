# Security Codemap

**Last Updated:** 2026-01-30
**Vulnerability Scanning:** Trivy Operator 0.31.0
**Runtime Security:** Falco 4.20.1

## Architecture

```
                    [Kubernetes API]
                          |
         +----------------+----------------+
         |                                 |
   [Trivy Operator]                  [Falco DaemonSet]
   (Vulnerability Scan)              (Runtime Detection)
         |                                 |
    +----+----+                     +------+------+
    |         |                     |             |
[trivy-server] [scan-jobs]    [falcosidekick]  [eBPF]
(DB cache)    (per workload)  (alert routing)  (syscalls)
    |              |                |
[Synology PVC]  [Reports]    +------+------+
(5Gi DB)        (CRDs)       |             |
                        [AlertManager] [Loki]
                        (notifications) (logs)
                              |
                        [Email Alerts]
```

## Trivy Operator

### Files

| File | Purpose |
|------|---------|
| `manifests/applications/trivy-operator.yaml` | ArgoCD Application |
| `manifests/base/trivy-operator/values.yaml` | Helm configuration |
| `manifests/base/trivy-operator/trivy-alerts.yaml` | PrometheusRules |
| `manifests/base/trivy-operator/namespace.yaml` | Namespace definition |
| `manifests/base/trivy-operator/kustomization.yaml` | Kustomize config |

### Configuration Highlights

```yaml
# manifests/base/trivy-operator/values.yaml

# Target all namespaces except system
targetNamespaces: ""
excludeNamespaces: "kube-system,kube-public,kube-node-lease"

operator:
  replicas: 1
  scanJobTimeout: 10m           # Increased for Pi nodes
  scanJobsConcurrentLimit: 3    # Reduced for resource constraints

  # All scanners enabled
  vulnerabilityScannerEnabled: true
  sbomGenerationEnabled: true
  configAuditScannerEnabled: true
  rbacAssessmentScannerEnabled: true
  infraAssessmentScannerEnabled: true
  clusterComplianceEnabled: true
  exposedSecretScannerEnabled: true

trivyServer:
  enabled: true
  persistence:
    enabled: true
    storageClass: "synology-iscsi-retain"
    size: 5Gi

trivy:
  mode: ClientServer
  severity: "CRITICAL,HIGH,MEDIUM"
  ignoreUnfixed: true

# Control-plane scanning
nodeCollector:
  tolerations:
    - key: node-role.kubernetes.io/control-plane
      operator: Exists
      effect: NoSchedule
```

### Reports (CRDs)

| CRD | Purpose |
|-----|---------|
| VulnerabilityReport | Container CVE findings |
| ConfigAuditReport | K8s config issues |
| ClusterComplianceReport | Compliance status |
| SbomReport | Software Bill of Materials |
| ExposedSecretReport | Detected secrets |
| RbacAssessmentReport | RBAC analysis |

### Querying Reports

```bash
# List vulnerability reports
kubectl get vulnerabilityreports -A

# Get critical vulnerabilities
kubectl get vulnerabilityreports -A -o json | jq '.items[] | select(.report.summary.criticalCount > 0) | .metadata.name'

# Get compliance status
kubectl get clustercompliancereports

# View specific report
kubectl describe vulnerabilityreport -n <namespace> <report-name>
```

## Falco

### Files

| File | Purpose |
|------|---------|
| `manifests/applications/falco.yaml` | ArgoCD Application |
| `manifests/base/falco/values.yaml` | Helm configuration |
| `manifests/base/falco/falco-alerts.yaml` | PrometheusRules |
| `manifests/base/falco/ingress.yaml` | Sidekick UI ingress |

### Configuration Highlights

```yaml
# manifests/base/falco/values.yaml

# Modern eBPF driver (efficient on ARM64)
driver:
  kind: modern_ebpf
  modernEbpf:
    bufSizePreset: 4

# Run on all nodes including control-plane
tolerations:
  - effect: NoSchedule
    key: node-role.kubernetes.io/control-plane
    operator: Exists

falco:
  jsonOutput: true
  logLevel: info
  priority: notice  # Reduce noise

# Custom homelab rules
customRules:
  homelab-rules.yaml: |-
    # Disable noisy rules
    - rule: Terminal shell in container
      override:
        enabled: replace
      enabled: false

    # Custom: Cryptocurrency mining detection
    - rule: Detect Cryptocurrency Mining
      condition: spawned_process and (proc.name in (xmrig, minerd, ...))
      priority: CRITICAL

    # Custom: Reverse shell detection
    - rule: Reverse Shell Detected
      condition: spawned_process and proc.cmdline contains "/dev/tcp"
      priority: CRITICAL

# Sidekick for alert routing
falcosidekick:
  enabled: true
  webui:
    enabled: true
  config:
    alertmanager:
      hostport: "http://alertmanager-operated.default:9093"
      minimumpriority: warning
    loki:
      hostport: "http://loki.loki:3100"
      minimumpriority: notice
```

### Components

| Component | Purpose | Replicas |
|-----------|---------|----------|
| falco | Syscall monitoring | DaemonSet (5) |
| falcosidekick | Alert routing | 1 |
| falcosidekick-ui | Web interface | 1 |

### Alert Routing

```
Falco Events
    |
    v
Falcosidekick
    |
    +---> AlertManager (warning+) ---> Email
    |
    +---> Loki (notice+) ---> Grafana
    |
    +---> Prometheus metrics
```

### Falco UI

- URL: https://falco.k8s.n37.ca
- Purpose: View recent security events
- Auth: None (internal only)

## Network Policies

### Trivy System

```yaml
# manifests/base/network-policies/trivy-system/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  ingress:
    # Prometheus scraping
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: default
      ports:
        - port: 8080  # metrics
        - port: 15008 # HBONE (mesh)
  egress:
    # DNS
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - port: 53
    # Kubernetes API
    - to:
        - ipBlock:
            cidr: 10.0.10.1/32
      ports:
        - port: 6443
    # Container registries
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - port: 443
```

### Falco

```yaml
# manifests/base/network-policies/falco/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  ingress:
    # Prometheus, ingress-nginx
    - from:
        - namespaceSelector: ...
      ports:
        - port: 8765  # metrics
        - port: 2801  # sidekick
        - port: 2802  # sidekick-ui
  egress:
    # AlertManager, Loki, K8s API
    - to: ...
      ports:
        - port: 9093  # alertmanager
        - port: 3100  # loki
        - port: 6443  # k8s api
```

## PrometheusRules

### Trivy Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| TrivyCriticalVulnerabilities | critical | criticalCount > 0 |
| TrivyHighVulnerabilities | warning | highCount > 10 |
| TrivyOperatorDown | critical | up == 0 for 5m |
| TrivyScanJobsFailing | warning | failed jobs > 5 |

### Falco Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| FalcoCriticalAlert | critical | priority == critical for 1m |
| FalcoWarningAlert | warning | priority == warning for 5m |
| FalcoRuleTriggered | info | any event |
| FalcoProcessDown | critical | up == 0 for 5m |
| FalcoHighEventRate | warning | rate > 100/min |

## Resource Usage

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|-------------|----------------|-----------|--------------|
| trivy-operator | 50m | 100Mi | 300m | 300Mi |
| trivy-server | 50m | 64Mi | 300m | 256Mi |
| falco | 50m | 128Mi | 500m | 512Mi |
| falcosidekick | 10m | 32Mi | 100m | 64Mi |
| falcosidekick-ui | 10m | 32Mi | 100m | 128Mi |

## Troubleshooting

### Trivy Issues

```bash
# Check operator status
kubectl get pods -n trivy-system

# View scan job logs
kubectl logs -n trivy-system -l app.kubernetes.io/name=trivy-operator

# Check trivy-server
kubectl logs -n trivy-system -l app.kubernetes.io/name=trivy

# Force rescan
kubectl delete vulnerabilityreport -n <namespace> <report-name>
```

### Falco Issues

```bash
# Check DaemonSet status
kubectl get pods -n falco -o wide

# View Falco logs
kubectl logs -n falco -l app.kubernetes.io/name=falco --tail=100

# Check sidekick connectivity
kubectl logs -n falco -l app.kubernetes.io/name=falcosidekick

# Verify eBPF driver
kubectl exec -n falco <falco-pod> -- falco --version
```

## Related Documentation

- [INDEX.md](INDEX.md) - Main codemap index
- [k8s-docs-n37 - Trivy](https://imcbeth.github.io/k8s-docs-n37/applications/trivy) - Trivy documentation
- [k8s-docs-n37 - Falco](https://imcbeth.github.io/k8s-docs-n37/applications/falco) - Falco documentation
