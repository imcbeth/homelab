# Homelab Infrastructure Codemap

**Last Updated:** 2026-01-30
**Cluster:** 5x Raspberry Pi 5 (16GB each, 80GB total)
**Kubernetes:** v1.35

## Architecture Overview

```
                              [External]
                                  |
                      +-----------+-----------+
                      |      Cloudflare       |
                      |     (Public DNS)      |
                      +-----------+-----------+
                                  |
                      +-----------+-----------+
                      |    UniFi Gateway      |
                      |   (10.0.0.0/8 VLANs)  |
                      +-----------+-----------+
                                  |
        +------------+------------+------------+------------+
        |            |            |            |            |
   [node01]     [node02]     [node03]     [node04]     [node05]
   control      worker       worker       worker       worker
   10.0.10.1    10.0.10.2    10.0.10.3    10.0.10.4    10.0.10.5

                    Kubernetes Cluster
        +------------------------------------------+
        |                                          |
        |  [tigera-operator] --> [calico-system]  |
        |  [istio-system] --> [ztunnel per node]  |
        |  [argocd] --> [27+ applications]        |
        |  [default] --> monitoring stack         |
        |  [loki] --> logging stack               |
        |  [falco] --> runtime security           |
        |  [trivy-system] --> vulnerability scan  |
        |                                          |
        +------------------------------------------+
                           |
               +-----------+-----------+
               |    Synology NAS       |
               |    10.0.1.204         |
               |  (iSCSI, SNMP, NFS)   |
               +-----------------------+
```

## Directory Structure

```
homelab/
├── manifests/
│   ├── applications/          # ArgoCD Application definitions
│   │   ├── argocd.yaml
│   │   ├── tigera-operator.yaml     # CNI (wave -100)
│   │   ├── kube-prometheus-stack.yaml
│   │   ├── falco.yaml              # Runtime security
│   │   ├── trivy-operator.yaml     # Vulnerability scanning
│   │   └── ... (27 total)
│   │
│   └── base/                  # Helm values and Kustomizations
│       ├── argocd/
│       ├── tigera-operator/   # Installation CR
│       ├── kube-prometheus-stack/
│       ├── falco/             # Values + custom rules
│       ├── trivy-operator/
│       ├── network-policies/  # Per-namespace policies
│       └── ... (25 directories)
│
├── secrets/                   # git-crypt encrypted (ArgoCD bootstrap only)
│
├── scripts/
│   └── validate-manifests.sh
│
├── apps/DockerFiles/          # Custom ARM64 container builds
│
├── docs/
│   └── CODEMAPS/             # Architecture documentation
│
└── .claude/notes/sessions/    # Session notes history
```

## Key Components

### CNI (Tigera Operator)

| File | Purpose |
|------|---------|
| `manifests/applications/tigera-operator.yaml` | ArgoCD Application (wave -100) |
| `manifests/base/tigera-operator/installation.yaml` | Installation CR with network config |

**Configuration:**
- Pod CIDR: 192.168.0.0/16
- Encapsulation: IPIP
- BGP: Enabled
- Typha: Topology spread across all nodes

### Service Mesh (Istio Ambient)

| File | Purpose |
|------|---------|
| `manifests/applications/istio-base.yaml` | CRDs and base resources |
| `manifests/applications/istio-cni.yaml` | CNI plugin for traffic capture |
| `manifests/applications/istiod.yaml` | Control plane |

**Status:**
- 29 pods with mTLS across 6 namespaces
- Resource usage: ~38m CPU, ~145Mi memory

### Monitoring Stack

| File | Purpose |
|------|---------|
| `manifests/applications/kube-prometheus-stack.yaml` | Prometheus, Grafana, AlertManager |
| `manifests/base/kube-prometheus-stack/values.yaml` | Helm values |
| `manifests/base/kube-prometheus-stack/*.yaml` | Dashboards, alerts, rules |

**ignoreDifferences Pattern:**
```yaml
# Grafana generates random password each render
ignoreDifferences:
  - group: ""
    kind: Secret
    name: kube-prometheus-stack-grafana
    jqPathExpressions:
      - .data["admin-password"]
syncPolicy:
  syncOptions:
    - RespectIgnoreDifferences=true
```

### Security (Trivy + Falco)

| File | Purpose |
|------|---------|
| `manifests/applications/trivy-operator.yaml` | Vulnerability scanning |
| `manifests/base/trivy-operator/values.yaml` | Scanner configuration |
| `manifests/applications/falco.yaml` | Runtime security |
| `manifests/base/falco/values.yaml` | Falco configuration |
| `manifests/base/falco/falco-alerts.yaml` | PrometheusRules |

### Network Policies

| Directory | Namespace |
|-----------|-----------|
| `manifests/base/network-policies/argo-workflows/` | argo-workflows |
| `manifests/base/network-policies/cert-manager/` | cert-manager |
| `manifests/base/network-policies/external-dns/` | external-dns |
| `manifests/base/network-policies/falco/` | falco |
| `manifests/base/network-policies/localstack/` | localstack |
| `manifests/base/network-policies/loki/` | loki |
| `manifests/base/network-policies/metallb-system/` | metallb-system |
| `manifests/base/network-policies/trivy-system/` | trivy-system |
| `manifests/base/network-policies/unipoller/` | unipoller |
| `manifests/base/network-policies/velero/` | velero |

## ArgoCD Sync Wave Order

| Wave | Application | Purpose |
|------|-------------|---------|
| -100 | tigera-operator | CNI foundation |
| -50 | argocd | Self-management |
| -35 | metal-lb, pi-hole | Networking |
| -30 | synology-csi | Storage |
| -25 | sealed-secrets | Secrets |
| -20 | unipoller | UniFi metrics |
| -15 | kube-prometheus-stack | Monitoring |
| -12 | loki | Logging |
| -11 | promtail | Log collection |
| -10 | cert-manager, external-dns, metrics-server | Certificates, DNS |
| -8 | argo-workflows | CI/CD |
| -7 | localstack | S3 mock |
| -5 | velero, falco | Backup, security |

## ArgoCD ignoreDifferences Patterns

### Operator-Managed Resources (Tigera)

Operators mutate resources at runtime. Use ignoreDifferences to prevent perpetual OutOfSync:

```yaml
ignoreDifferences:
  - group: operator.tigera.io
    kind: Installation
    jsonPointers:
      - /status
      - /spec/cni
      - /spec/registry
      # ... operator-managed fields
  - group: apiextensions.k8s.io
    kind: CustomResourceDefinition
    jqPathExpressions:
      - .metadata.annotations
      - .spec.preserveUnknownFields
```

### Generated Secrets (Grafana)

Helm charts that generate random values need ignoreDifferences:

```yaml
ignoreDifferences:
  - group: ""
    kind: Secret
    name: kube-prometheus-stack-grafana
    jqPathExpressions:
      - .data["admin-password"]
```

**Critical:** Add `RespectIgnoreDifferences=true` to syncOptions for automated sync.

## External Dependencies

| Service | Purpose | Location |
|---------|---------|----------|
| Synology NAS | iSCSI storage, SNMP metrics | 10.0.1.204 |
| Cloudflare | Public DNS, API tokens | cloudflare.com |
| UniFi Controller | Internal DNS, network metrics | 10.0.1.200:8443 |
| Backblaze B2 | Velero backup storage | b2.backblaze.com |
| Let's Encrypt | TLS certificates | acme-v02.api.letsencrypt.org |

## Related Documentation

- [TODO.md](/Users/imcbeth/homelab/TODO.md) - Project roadmap and completion tracking
- [Hardware.md](/Users/imcbeth/homelab/Hardware.md) - Hardware specifications
- [network-info.md](/Users/imcbeth/homelab/network-info.md) - Network architecture
- [k8s-docs-n37](https://imcbeth.github.io/k8s-docs-n37/) - Comprehensive documentation site
