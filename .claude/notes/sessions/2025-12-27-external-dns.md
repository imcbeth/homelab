# 2025-12-27 (Late Evening): External-DNS Deployment and Troubleshooting

**Completed Work:**
- Deployed external-dns with dual provider support (Cloudflare + UniFi webhook)
- Fixed missing EndpointSlice RBAC permissions
- Fixed webhook service port mapping configuration
- Verified DNS record creation in both Cloudflare and UniFi

**Pull Requests:**
- **PR #124:** [Merged] Fix: Add EndpointSlice RBAC permissions for external-dns
- **PR #125:** [Merged] Fix: Correct webhook service port mapping for external-dns

**Issue 1: Missing EndpointSlice RBAC Permissions**
```
level=fatal msg="failed to sync *v1.EndpointSlice: context deadline exceeded"
```
Solution: Add EndpointSlice permissions to ClusterRole:
```yaml
- apiGroups: ["discovery.k8s.io"]
  resources: ["endpointslices"]
  verbs: ["get", "watch", "list"]
```

**Issue 2: Incorrect Webhook Service Port Mapping**
```
level=fatal msg="failed to connect to webhook: dial tcp 10.106.73.112:8888: connect: connection refused"
```
Solution: Fix service port mappings - port 8888 needs targetPort `http-wh`

**Split-Horizon DNS Configuration:**

**Cloudflare Provider (Public DNS):**
- Domain: k8s.n37.ca
- Records: A records pointing to public IP
- TXT Owner: external-dns-cloudflare

**UniFi Provider (Internal DNS):**
- Domain: k8s.n37.ca
- Records: A records pointing to MetalLB IPs (10.0.50.x)
- Webhook: kashalls/external-dns-unifi-webhook:v0.7.0
- TXT Owner: external-dns-unifi

**Files Modified:**
- `manifests/base/external-dns/rbac.yaml` - Added EndpointSlice permissions
- `manifests/base/external-dns/webhook-unifi-service.yaml` - Fixed port mapping
- `manifests/base/argocd/argo-nginx-ingress.yaml` - Added external-dns annotations
- `manifests/base/kube-prometheus-stack/values.yaml` - Added external-dns annotations
