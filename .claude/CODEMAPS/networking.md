# Networking Codemap

**Last Updated:** 2026-01-30
**CNI:** Calico v3.29.2 (Tigera Operator)
**Service Mesh:** Istio Ambient 1.x

## Architecture

```
                    [External Traffic]
                           |
                    [ingress-nginx]
                           |
              +------------+------------+
              |                         |
        [MetalLB]                 [cert-manager]
    (LoadBalancer IPs)          (TLS Certificates)
              |                         |
    +---------+---------+    +----------+----------+
    |                   |    |                     |
[Pi-hole]         [Services]               [external-dns]
(Internal DNS)    (ClusterIP)           (Cloudflare + UniFi)
                        |
                  [Calico CNI]
              (Pod Networking, Policy)
                        |
            +-----------+-----------+
            |                       |
     [calico-node]           [calico-typha]
    (DaemonSet x5)          (Deployment, spread)
            |
     [Istio ztunnel]
    (mTLS per node)
```

## Tigera Operator (CNI)

### Files

| File | Purpose |
|------|---------|
| `manifests/applications/tigera-operator.yaml` | ArgoCD Application |
| `manifests/base/tigera-operator/installation.yaml` | Installation CR |

### Application Definition

```yaml
# manifests/applications/tigera-operator.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: tigera-operator
  annotations:
    argocd.argoproj.io/sync-wave: "-100"  # Deploy first
spec:
  sources:
    # Operator from official Calico repo
    - repoURL: https://github.com/projectcalico/calico.git
      targetRevision: v3.29.2
      path: manifests
      directory:
        include: 'tigera-operator.yaml'
    # Installation CR from homelab
    - repoURL: git@github.com:imcbeth/homelab.git
      path: manifests/base/tigera-operator
  syncPolicy:
    syncOptions:
      - ServerSideApply=true
      - RespectIgnoreDifferences=true
  ignoreDifferences:
    # Operator mutates Installation CR at runtime
    - group: operator.tigera.io
      kind: Installation
      jsonPointers:
        - /status
        - /spec/cni
        - /spec/flexVolumePath
        - /spec/registry
        # ... (many more)
```

### Installation CR Configuration

```yaml
# manifests/base/tigera-operator/installation.yaml
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  variant: Calico
  calicoNetwork:
    bgp: Enabled
    ipPools:
      - name: default-ipv4-ippool
        cidr: 192.168.0.0/16
        encapsulation: IPIP
        natOutgoing: Enabled
        blockSize: 26
    nodeAddressAutodetectionV4:
      kubernetes: NodeInternalIP
  registry: docker.io/
  controlPlaneReplicas: 1
  # Typha spread across all nodes
  typhaDeployment:
    spec:
      template:
        spec:
          topologySpreadConstraints:
            - maxSkew: 1
              topologyKey: kubernetes.io/hostname
              whenUnsatisfiable: ScheduleAnyway
```

### Namespaces

| Namespace | Components |
|-----------|------------|
| tigera-operator | Tigera operator deployment |
| calico-system | calico-node, calico-typha, calico-kube-controllers |
| calico-apiserver | Calico API server (optional) |

## Network Policies

### Directory Structure

```
manifests/base/network-policies/
├── kustomization.yaml
├── argo-workflows/
│   └── network-policy.yaml
├── cert-manager/
│   └── network-policy.yaml
├── external-dns/
│   └── network-policy.yaml
├── falco/
│   └── network-policy.yaml
├── localstack/
│   └── network-policy.yaml
├── loki/
│   └── network-policy.yaml
├── metallb-system/
│   └── network-policy.yaml
├── trivy-system/
│   └── network-policy.yaml
├── unipoller/
│   └── network-policy.yaml
└── velero/
    └── network-policy.yaml
```

### Policy Pattern (Istio Ambient)

When namespace is in Istio Ambient mesh, policies must allow HBONE port 15008:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: example-policy
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # From istio-system (ztunnel)
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: istio-system
      ports:
        - port: 15008  # HBONE
        - port: <app-port>
    # From source namespace (transparent proxy preserves source IP)
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: <source-namespace>
      ports:
        - port: 15008  # HBONE
        - port: <app-port>
```

## MetalLB

### Files

| File | Purpose |
|------|---------|
| `manifests/applications/metal-lb.yaml` | ArgoCD Application |
| `manifests/base/metal-lb/values.yaml` | Helm values |

### IP Address Pool

- Range: 10.0.10.200-10.0.10.250
- Mode: Layer 2 (ARP-based)

## External DNS

### Files

| File | Purpose |
|------|---------|
| `manifests/applications/external-dns.yaml` | ArgoCD Application |
| `manifests/base/external-dns/values.yaml` | Helm values |
| `manifests/base/external-dns/cloudflare-*.yaml` | Cloudflare provider |
| `manifests/base/external-dns/unifi-*.yaml` | UniFi webhook provider |

### Providers

| Provider | Purpose | Domain |
|----------|---------|--------|
| Cloudflare | Public DNS | *.k8s.n37.ca |
| UniFi Webhook | Internal DNS | *.k8s.n37.ca (internal) |

## Istio Ambient

### Files

| File | Purpose |
|------|---------|
| `manifests/applications/istio-base.yaml` | CRDs |
| `manifests/applications/istio-cni.yaml` | CNI plugin |
| `manifests/applications/istiod.yaml` | Control plane |
| `manifests/base/istio/values.yaml` | Helm values |

### Meshed Namespaces

| Namespace | Pod Count | Label |
|-----------|-----------|-------|
| default | 15 | `istio.io/dataplane-mode: ambient` |
| loki | 10 | `istio.io/dataplane-mode: ambient` |
| argo-workflows | 2 | `istio.io/dataplane-mode: ambient` |
| localstack | 1 | `istio.io/dataplane-mode: ambient` |
| unipoller | 1 | `istio.io/dataplane-mode: ambient` |
| trivy-system | 2 | `istio.io/dataplane-mode: ambient` |

### Resource Usage

| Component | Instances | CPU | Memory |
|-----------|-----------|-----|--------|
| istiod | 1 | ~3m | ~39Mi |
| istio-cni-node | 5 | ~5m | ~68Mi |
| ztunnel | 5 | ~30m | ~38Mi |
| **Total** | - | **~38m** | **~145Mi** |

## Troubleshooting

### Calico Issues

```bash
# Check Calico status
kubectl get installation default -o yaml
kubectl get pods -n calico-system

# Verify Typha distribution
kubectl get pods -n calico-system -l k8s-app=calico-typha -o wide

# Check calico-node logs
kubectl logs -n calico-system -l k8s-app=calico-node --tail=50

# Verify IP pool
kubectl get ippool -o yaml
```

### NetworkPolicy Issues

```bash
# List policies in namespace
kubectl get networkpolicy -n <namespace>

# Describe policy
kubectl describe networkpolicy -n <namespace> <policy-name>

# Test connectivity (from pod)
kubectl exec -it <pod> -- wget -O- http://<service>:<port>
```

### Istio Ambient Issues

```bash
# Check ztunnel status
kubectl get pods -n istio-system -l app=ztunnel

# View ztunnel logs
kubectl logs -n istio-system -l app=ztunnel --tail=50

# Check namespace labels
kubectl get namespace -L istio.io/dataplane-mode

# Verify mTLS
istioctl proxy-status
```

## Related Documentation

- [INDEX.md](INDEX.md) - Main codemap index
- [k8s-docs-n37 - Istio](https://imcbeth.github.io/k8s-docs-n37/applications/istio) - Istio documentation
- [k8s-docs-n37 - Network Policies](https://imcbeth.github.io/k8s-docs-n37/guides/network-policies) - Policy documentation
