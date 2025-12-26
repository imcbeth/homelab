## External-DNS Configuration

External-DNS automatically manages DNS records for Kubernetes resources.

### Dual Provider Setup

This deployment runs **two external-dns instances**:

1. **Cloudflare** - Public DNS for `k8s.n37.ca`
2. **RFC2136 (UniFi)** - Internal DNS for `k8s.n37.ca`

### Configuration Steps

#### 1. Cloudflare (Already Configured)

The Cloudflare deployment reuses the API token from `cert-manager`:
- ✅ Token: `cloudflare-api-token-secret`
- ✅ Domain: `k8s.n37.ca`
- ✅ Permissions: DNS:Edit

**No additional configuration needed** - uses the same token as cert-manager.

#### 2. UniFi UDR7 RFC2136 Setup

**On UniFi Controller (10.0.1.1):**

1. Navigate to: **Settings → System → Advanced**
2. Enable **RFC2136 Dynamic DNS**
3. Create a TSIG key:
   - **Key Name:** `external-dns`
   - **Algorithm:** `hmac-sha256`
   - Click **Generate** to create a secret key
   - **Save** the configuration

4. Copy the TSIG credentials and update `secret-rfc2136.yaml`:
   ```yaml
   stringData:
     tsig-keyname: external-dns
     tsig-secret: <base64-encoded-key-from-unifi>
     tsig-algorithm: hmac-sha256
   ```

5. Apply the updated secret:
   ```bash
   kubectl apply -f manifests/base/external-dns/secret-rfc2136.yaml
   ```

6. Restart the RFC2136 deployment:
   ```bash
   kubectl rollout restart deployment/external-dns-rfc2136 -n external-dns
   ```

### How It Works

**Watched Resources:**
- ✅ **Ingress** resources with hostnames
- ✅ **LoadBalancer Services** with MetalLB IPs

**Example Ingress:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.k8s.n37.ca
spec:
  rules:
  - host: myapp.k8s.n37.ca
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80
```

**What Happens:**
1. external-dns detects the Ingress
2. **Cloudflare** creates `myapp.k8s.n37.ca` → MetalLB IP (public)
3. **UniFi** creates `myapp.k8s.n37.ca` → MetalLB IP (internal)
4. TXT records track ownership: `external-dns-myapp.k8s.n37.ca`

**Example LoadBalancer Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    external-dns.alpha.kubernetes.io/hostname: service.k8s.n37.ca
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
```

### DNS Policy

**Mode:** `upsert-only`
- ✅ Creates new DNS records
- ✅ Updates existing DNS records
- ❌ **Does NOT delete** DNS records (safe mode)

This prevents accidental deletion of manually created DNS records.

### Monitoring

**Check external-dns logs:**
```bash
# Cloudflare provider
kubectl logs -n external-dns deployment/external-dns-cloudflare -f

# RFC2136/UniFi provider
kubectl logs -n external-dns deployment/external-dns-rfc2136 -f
```

**Check managed DNS records:**
```bash
# List all DNS records created by external-dns
kubectl get ingress -A
kubectl get svc -A --field-selector spec.type=LoadBalancer

# Check TXT ownership records
dig TXT external-dns-argocd.k8s.n37.ca
```

### Troubleshooting

**Cloudflare records not created:**
1. Check logs: `kubectl logs -n external-dns deployment/external-dns-cloudflare`
2. Verify API token: `kubectl get secret cloudflare-api-token -n external-dns`
3. Ensure Cloudflare zone includes `k8s.n37.ca`
4. Check Cloudflare API token permissions (DNS:Edit)

**UniFi records not created:**
1. Check logs: `kubectl logs -n external-dns deployment/external-dns-rfc2136`
2. Verify RFC2136 enabled on UniFi controller
3. Verify TSIG credentials: `kubectl get secret rfc2136-credentials -n external-dns -o yaml`
4. Test RFC2136 access from cluster:
   ```bash
   kubectl exec -n external-dns deployment/external-dns-rfc2136 -- \
     nslookup -type=SOA n37.ca 10.0.1.1
   ```

**DNS records not syncing:**
- Check domain filter: `--domain-filter=k8s.n37.ca`
- Verify ingress has correct hostname
- Check sync interval (default: 1 minute)
- Ensure resources are in correct namespace

### Security

**RBAC Permissions:**
- ClusterRole with read-only access to Ingress, Service, Pod resources
- No write permissions to Kubernetes resources
- Separate ServiceAccounts for Cloudflare and RFC2136

**Secrets:**
- `cloudflare-api-token`: Cloudflare API token (shared with cert-manager)
- `rfc2136-credentials`: UniFi TSIG authentication

**Network Security:**
- Cloudflare: HTTPS API calls to Cloudflare
- RFC2136: DNS over TCP/UDP to UniFi controller (10.0.1.1:53)

### Resource Usage

**Per Deployment:**
- CPU: 50m request, 100m limit
- Memory: 64Mi request, 128Mi limit
- Total for both: ~100m CPU, ~128Mi memory

Minimal overhead for automatic DNS management!

### References

- [external-dns Documentation](https://kubernetes-sigs.github.io/external-dns/)
- [Cloudflare Provider](https://kubernetes-sigs.github.io/external-dns/v0.15.0/tutorials/cloudflare/)
- [RFC2136 Provider](https://kubernetes-sigs.github.io/external-dns/v0.15.0/tutorials/rfc2136/)
- [UniFi RFC2136 Setup](https://help.ui.com/hc/en-us/articles/204976324-UniFi-Gateway-Dynamic-DNS)
