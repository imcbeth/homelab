# External-DNS UniFi Webhook Setup Guide

## Overview

This setup uses [lexfrei/external-dns-unifios-webhook](https://github.com/lexfrei/external-dns-unifios-webhook) to integrate External-DNS with UniFi OS DNS management, enabling automatic DNS record creation for Kubernetes Ingress and LoadBalancer services.

## Prerequisites

- **UniFi OS**: Version 4.3.9 or higher
- **UniFi Network**: Version 9.4.19 or higher
- **External-DNS**: Version 0.20.0 or higher
- **UniFi API Key**: With DNS management permissions

## UniFi Controller Configuration

### 1. Create API Key

1. Log into your UniFi Console (e.g., https://10.0.1.1)
2. Navigate to **Settings** → **Integrations** → **API**
3. Click **Create API Key**
4. **Name**: `external-dns-k8s`
5. **Permissions**: Ensure DNS management permissions are granted
6. **Copy the API key** (you won't be able to see it again)

### 2. Verify DNS Settings

1. Navigate to **Settings** → **Networks** → **Default** (or your network)
2. Ensure **DHCP DNS Server** is enabled
3. Note the DNS domain (should match `k8s.n37.ca` in this setup)

## Kubernetes Secret Configuration

Update the secret with your UniFi credentials:

```bash
# Edit the secret file
vim manifests/base/external-dns/secret-unifi.yaml
```

Replace the placeholder values:

```yaml
stringData:
  UNIFI_HOST: "https://10.0.1.1"  # Your UniFi controller URL
  UNIFI_API_KEY: "YOUR_ACTUAL_API_KEY_HERE"  # API key from step 1
  UNIFI_SITE_NAME: "default"  # Usually "default", check your site name
  UNIFI_TLS_INSECURE: "true"  # Set to "false" if using valid TLS cert
```

**IMPORTANT**: After updating, encrypt the secret file:

```bash
# Encrypt with git-crypt (if using)
git-crypt lock
git-crypt unlock

# Or use sealed-secrets/SOPS depending on your setup
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                              │
│  ┌────────────────┐         ┌──────────────────────┐        │
│  │ Ingress/       │         │  external-dns        │        │
│  │ LoadBalancer   │────────▶│  (webhook provider)  │        │
│  │ Services       │         └──────────┬───────────┘        │
│  └────────────────┘                    │                    │
│                                        │ HTTP               │
│                            ┌───────────▼──────────┐         │
│                            │  UniFi Webhook       │         │
│                            │  (lexfrei)           │         │
│                            └──────────┬───────────┘         │
│                                       │                     │
└───────────────────────────────────────┼─────────────────────┘
                                        │
                                        │ UniFi API
                                        │ (HTTPS)
                                        ▼
                            ┌──────────────────────┐
                            │   UniFi Controller   │
                            │   (10.0.1.1)         │
                            │                      │
                            │   DNS Records        │
                            │   - A Records        │
                            │   - AAAA Records     │
                            │   - CNAME Records    │
                            │   - TXT Records      │
                            └──────────────────────┘
```

## Components

### 1. UniFi Webhook Provider

- **Image**: `ghcr.io/lexfrei/external-dns-unifios-webhook:v0.2.0`
- **Port**: 8080 (HTTP API), 8888 (Health checks)
- **Features**:
  - Prometheus metrics on port 8080
  - OpenTelemetry instrumentation
  - Structured JSON logging
  - Health/readiness probes

### 2. External-DNS

- **Image**: `registry.k8s.io/external-dns/external-dns:v0.20.0`
- **Provider**: webhook
- **Webhook URL**: `http://external-dns-unifi-webhook:8080`
- **Sources**: Ingress, Service (LoadBalancer)
- **Domain Filter**: `k8s.n37.ca`

### 3. Supported DNS Record Types

- **A**: IPv4 address records
- **AAAA**: IPv6 address records
- **CNAME**: Canonical name records
- **TXT**: Text records (for ownership tracking)

## Configuration Parameters

### External-DNS Arguments

```yaml
- --provider=webhook
- --webhook-provider-url=http://external-dns-unifi-webhook:8080
- --source=ingress
- --source=service
- --domain-filter=k8s.n37.ca
- --policy=upsert-only  # Won't delete existing records
- --registry=txt  # Use TXT records for ownership tracking
- --txt-owner-id=external-dns-unifi
- --interval=1m  # Sync every minute
```

### Webhook Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `UNIFI_HOST` | UniFi controller URL | `https://10.0.1.1` |
| `UNIFI_API_KEY` | API key with DNS permissions | `abcd1234...` |
| `UNIFI_SITE_NAME` | Site name in UniFi | `default` |
| `UNIFI_TLS_INSECURE` | Skip TLS verification (NOT recommended; set to `true` only as a last resort, e.g. for testing/self-signed certs, with full understanding of the security risk) | `false` |
| `LOG_LEVEL` | Logging level | `info` |
| `LOG_FORMAT` | Log format | `json` |

## Testing

### 1. Deploy External-DNS

```bash
# Apply via ArgoCD (automatic if auto-sync enabled)
# Or manually:
kubectl apply -k manifests/base/external-dns/
```

### 2. Verify Webhook is Running

```bash
# Check webhook deployment
kubectl get deployment -n external-dns external-dns-unifi-webhook

# Check webhook logs
kubectl logs -n external-dns deployment/external-dns-unifi-webhook

# Check external-dns logs
kubectl logs -n external-dns deployment/external-dns-unifi
```

### 3. Create Test Service

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: test-external-dns
  namespace: default
  annotations:
    external-dns.alpha.kubernetes.io/hostname: test.k8s.n37.ca
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
  selector:
    app: nginx
EOF
```

### 4. Verify DNS Record

```bash
# Wait ~1 minute for sync

# Check external-dns logs
kubectl logs -n external-dns deployment/external-dns-unifi | grep test.k8s.n37.ca

# Query DNS
nslookup test.k8s.n37.ca 10.0.0.200

# Check in UniFi Console
# Settings → Networks → DNS → Records
```

## Troubleshooting

### Webhook Not Starting

**Problem**: Webhook pod fails to start

**Solutions**:
```bash
# Check pod status
kubectl describe pod -n external-dns -l app.kubernetes.io/name=external-dns-unifi-webhook

# Common issues:
# - Invalid API key
# - Network connectivity to UniFi controller
# - TLS certificate issues (fix UniFi certificate/CA config; use UNIFI_TLS_INSECURE=true only as a temporary, insecure workaround for testing)
```

### DNS Records Not Created

**Problem**: Services/Ingresses not creating DNS records

**Solutions**:
```bash
# Check external-dns logs
kubectl logs -n external-dns deployment/external-dns-unifi

# Verify domain filter matches
# --domain-filter=k8s.n37.ca should match your ingress hostname

# Check service annotations
kubectl get svc -A -o yaml | grep external-dns

# Verify UniFi API permissions
# API key must have DNS management permissions
```

### UniFi API Connection Errors

**Problem**: Webhook cannot connect to UniFi controller

**Solutions**:
```bash
# Test connectivity from cluster (temporary debugging only)
# In production, use a valid certificate and enable TLS verification
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl https://10.0.1.1

# Check secret configuration
kubectl get secret -n external-dns unifi-credentials -o yaml

# Verify UNIFI_HOST includes https://
# For production, keep TLS verification enabled with a trusted (public or internal) CA
# Use UNIFI_TLS_INSECURE="true" only as a temporary workaround for debugging self-signed certs
```

### Duplicate or Invalid Records

**Problem**: Duplicate CNAME or invalid records

**Solution**:
- UniFi uses dnsmasq which doesn't support wildcard CNAME or duplicate entries
- Ensure only one record per hostname
- Use A/AAAA records instead of CNAME when possible

## Monitoring

### Prometheus Metrics

The webhook exposes Prometheus metrics on port 8080:

```bash
# Port-forward to access metrics
kubectl port-forward -n external-dns svc/external-dns-unifi-webhook 8080:8080

# View metrics
curl http://localhost:8080/metrics
```

### Health Checks

```bash
# Liveness probe
kubectl exec -n external-dns deployment/external-dns-unifi-webhook -- \
  wget -O- http://localhost:8888/healthz

# Readiness probe
kubectl exec -n external-dns deployment/external-dns-unifi-webhook -- \
  wget -O- http://localhost:8888/readyz
```

## Limitations

1. **No Wildcard CNAME**: dnsmasq backend limitation
2. **No Duplicate CNAME**: Only one CNAME record per name
3. **5MB Request Limit**: ~25,000 DNS records maximum
4. **API Key Rotation**: Manual secret update required

## Migration from RFC2136

If you previously used the RFC2136-based External-DNS setup:

1. **Note**: In this repository, the RFC2136 manifests (including `deployment-rfc2136.yaml`) have already been removed and replaced by the UniFi webhook provider.
2. **Remove any existing RFC2136 deployment** from your cluster (if still running).
3. **Ensure your own manifests/kustomization** no longer reference the old RFC2136 resources.
4. **Deploy the UniFi webhook-based External-DNS** as described above.
5. **Verify DNS resolution** for your services/ingresses.

   ```bash
   # Example: remove legacy RFC2136 External-DNS (adjust namespace/name as needed)
   kubectl delete deployment external-dns-rfc2136 -n external-dns || true

   # If you still have a local copy of the old manifests,
   # remove any RFC2136 entries from your kustomization.yaml.
   ```

## References

- **Webhook Project**: https://github.com/lexfrei/external-dns-unifios-webhook
- **External-DNS Docs**: https://github.com/kubernetes-sigs/external-dns
- **UniFi API Docs**: https://ubntwiki.com/products/software/unifi-controller/api
- **Alternative Provider**: https://github.com/kashalls/external-dns-unifi-webhook (v0.7.0, October 2025)

## Support

For issues specific to the webhook provider, please open an issue at:
https://github.com/lexfrei/external-dns-unifios-webhook/issues

For general External-DNS questions, see:
https://github.com/kubernetes-sigs/external-dns/issues
