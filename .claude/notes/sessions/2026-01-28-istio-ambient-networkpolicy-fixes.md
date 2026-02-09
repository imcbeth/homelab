# 2026-01-28: Istio Ambient NetworkPolicy Fixes

**Context:** Continued from service mesh evaluation session. Istio Ambient was selected over Linkerd and migrated to ArgoCD management. This session focused on fixing NetworkPolicy issues preventing mesh communication.

## Completed Work

### NetworkPolicy Fixes for Istio Ambient Transparent Proxy

Fixed critical connectivity issues in meshed namespaces. The key learning: **Istio Ambient uses transparent proxy which preserves source IPs**. NetworkPolicies must allow HBONE port 15008 from the actual source namespace, not just istio-system.

**Pull Requests:**
- **PR #316:** fix: Correct HBONE ingress selector for Istio ambient mesh
  - Changed selector from `istio.io/dataplane-mode: ambient` to `kubernetes.io/metadata.name: istio-system`

- **PR #317:** fix: Allow application ports from istio-system for ambient mesh
  - Added app ports (3100, 4566, 9090, etc.) from istio-system for ztunnel-originated connections

- **PR #318:** fix: Add HBONE port 15008 for Istio ambient transparent proxy
  - Key fix: Added port 15008 to all cross-namespace and intra-namespace rules
  - Transparent proxy means source IP is preserved, so allow from source namespace

### Mesh Status

**29 pods across 6 namespaces now have mTLS (HBONE protocol):**
- default (15 pods) - Prometheus, Grafana, AlertManager, exporters
- loki (10 pods) - Loki, Promtail, loki-canary
- argo-workflows (2 pods) - Server and controller
- localstack (1 pod) - S3 emulator
- unipoller (1 pod) - UniFi metrics
- trivy-system (2 pods) - Vulnerability scanner

### Resource Usage (Current)

| Component | Instances | CPU | Memory |
|-----------|-----------|-----|--------|
| istiod | 1 | ~3m | ~39Mi |
| istio-cni-node | 5 | ~5m | ~68Mi |
| ztunnel | 5 | ~30m | ~38Mi |
| **Total** | - | **~38m** | **~145Mi** |

### Waypoint Proxy Decision

**Recommendation: Skip waypoints for now**
- L4 mTLS is working (current setup provides encryption and identity)
- Waypoints add extra Envoy pods per namespace
- Only needed for L7 features (HTTP routing, retries, header-based auth)
- Can be added later to specific namespaces if L7 features are required

## Documentation Updated

- Updated `k8s-docs-n37/docs/applications/istio.md`:
  - Comprehensive NetworkPolicy requirements for transparent proxy
  - HBONE troubleshooting guide
  - Current resource measurements
  - Updated meshed namespaces list

## Key Technical Learning

**Istio Ambient Transparent Proxy Architecture:**
1. ztunnel intercepts pod traffic using TPROXY
2. Source IP is preserved (not replaced with ztunnel IP)
3. HBONE tunnel uses port 15008 for mTLS between ztunnels
4. NetworkPolicies see the original source namespace, not istio-system
5. Both ingress AND egress rules need port 15008 for mesh communication

**NetworkPolicy Pattern for Meshed Namespaces:**
```yaml
ingress:
  # From istio-system (ztunnel terminates tunnel)
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

## Files Modified

**homelab repo:**
- `manifests/base/network-policies/loki/network-policy.yaml`
- `manifests/base/network-policies/localstack/network-policy.yaml`
- `manifests/base/network-policies/argo-workflows/network-policy.yaml`
- `manifests/base/network-policies/unipoller/network-policy.yaml`
- `manifests/base/network-policies/trivy-system/network-policy.yaml`

**k8s-docs-n37 repo:**
- `docs/applications/istio.md`

## Known Issue (Pre-existing)

Loki returns HTTP 400 for some log streams with >15 labels. This is a Loki label limit configuration issue, not a mesh issue. The mesh is working correctly (connections succeed, application returns 400).
