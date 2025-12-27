# Network Information

## Overview

This document describes the network architecture for the Raspberry Pi Kubernetes homelab cluster.

---

## VLAN Configuration

| Name | VLAN ID | Subnet | Gateway | Purpose |
|------|---------|---------|---------|---------|
| Home | 1 | 10.0.1.0/24 | 10.0.1.1 | Primary home network, NAS, gateway |
| IoT | 2 | 10.0.2.0/24 | 10.0.2.1 | Internet of Things devices |
| Kubernetes | 10 | 10.0.10.0/24 | 10.0.10.1 | Kubernetes cluster nodes and services |
| Work | 100 | 10.0.100.0/24 | 10.0.100.1 | Work devices and VPN |
| Guest | 99 | 10.0.99.0/24 | 10.0.99.1 | Guest network |

---

## Wireless Networks

| SSID | VLAN ID | Subnet | Security | Notes |
|------|---------|---------|----------|-------|
| micro-net | 1 | 10.0.1.0/24 | WPA3 | Primary home network |
| micro-iot | 2 | 10.0.2.0/24 | WPA2 | IoT devices (legacy compatibility) |
| micro-guest | 99 | 10.0.99.0/24 | WPA3 | Guest access, isolated |

---

## Network Infrastructure

### Gateway/Router
- **Device:** UniFi Dream Router (UDR7)
- **IP Address:** 10.0.1.1
- **Management:** UniFi Network Application
- **Features:**
  - VLAN routing between subnets
  - DNS forwarding to Pi-hole
  - RFC2136 support for dynamic DNS (to be configured)
  - DHCP server for all VLANs

### Switch
- **Device:** UniFi USW-Pro-24-PoE
- **Management IP:** 10.0.1.x (managed via UniFi Controller)
- **Power:** Powers all 5 Raspberry Pi nodes via PoE
- **Previous:** TP-Link TL-SG1008MP (replaced December 2025)

### DNS Server
- **Primary:** Pi-hole (deployed in Kubernetes)
- **IP Address:** 10.0.0.200 (MetalLB LoadBalancer, pending deployment)
- **Upstream:** Cloudflare DNS (1.1.1.1, 1.0.0.1)
- **Features:** Ad-blocking, DHCP, local DNS overrides

---

## Kubernetes Cluster Network (VLAN 10)

### Node IP Addresses

| Hostname | IP Address | MAC Address | Role | PoE Port |
|----------|------------|-------------|------|----------|
| control-plane | 10.0.10.214 | - | Control Plane | - |
| node01 | 10.0.10.211 | - | Worker | - |
| node02 | 10.0.10.212 | - | Worker | - |
| node03 | 10.0.10.213 | - | Worker | - |
| node04 | 10.0.10.220 | - | Worker | - |

**Note:** All nodes are Raspberry Pi 5 (16GB) running Ubuntu 24.04.3 LTS with Kubernetes v1.35.0

### Kubernetes Networking

#### CNI (Container Network Interface)
- **Plugin:** Calico v3.31.3
- **Pod CIDR:** 192.168.0.0/16 (default Calico)
- **Network Policy:** Enabled (not yet configured)
- **IP-in-IP:** Enabled for cross-node pod communication
- **Known Limitation:** Cannot route from pod network to hostNetwork pods on different nodes

#### Service Network
- **Service CIDR:** 10.96.0.0/12 (Kubernetes default)
- **DNS Service:** CoreDNS at 10.96.0.10
- **Cluster Domain:** cluster.local

### MetalLB Load Balancer

- **Mode:** Layer 2
- **IP Pool:** 10.0.10.10 - 10.0.10.99 (90 available IPs)
- **IP Pool Name:** first-pool
- **Auto-assign:** Enabled
- **Status:**
  - Assigned IPv4: 1 (only ingress-nginx-controller; pi-hole LoadBalancer is still pending and not yet assigned from this pool)
  - Available IPv4: 89

#### Allocated LoadBalancer IPs

| Service | Namespace | IP Address | Ports | Purpose |
|---------|-----------|------------|-------|---------|
| ingress-nginx-controller | ingress-nginx | 10.0.10.10 | 80, 443 | Main ingress controller |
| pi-hole | pihole | 10.0.10.11 | 53, 80, 443 | DNS/DHCP (pending) |

### Ingress Configuration

- **Controller:** nginx-ingress v1.14.1
- **External IP:** 10.0.10.10 (via MetalLB)
- **TLS:** Let's Encrypt via cert-manager (Cloudflare DNS-01 challenge)
- **Public Domain:** k8s.n37.ca
- **IngressClass:** nginx (default)

#### Active Ingresses

| Host | Namespace | Service | TLS | Status |
|------|-----------|---------|-----|--------|
| argocd.k8s.n37.ca | argocd | argocd-server | ✅ | Active |
| grafana.k8s.n37.ca | default | kube-prometheus-stack-grafana | ✅ | Active |
| localstack.k8s.n37.ca | localstack | localstack | ✅ | Active |

---

## External Services (VLAN 1 - Home Network)

| Service | IP Address | Purpose | Access |
|---------|------------|---------|--------|
| UniFi Gateway (UDR7) | 10.0.1.1 | Router, DHCP, DNS forwarder | HTTPS |
| Synology NAS (DS925+) | 10.0.1.204 | iSCSI storage, NFS, SMB | HTTPS, iSCSI |
| UniFi Controller | 10.0.1.1 | Network management | Built into UDR7 |

### Synology NAS Network Configuration
- **Hostname:** synology-nas (local DNS)
- **Management:** HTTPS on port 5001
- **iSCSI Target:** 10.0.1.204:3260
- **Services:**
  - iSCSI: Provides storage to Kubernetes via Synology CSI
  - SMB/NFS: File sharing
  - SNMP: Monitored by SNMP exporter (SNMPv3, port 161)
  - Docker: Container services (not used by K8s)

---

## DNS Configuration

### Internal DNS (Kubernetes)

- **Service:** CoreDNS
- **ClusterIP:** 10.96.0.10
- **Zone:** cluster.local
- **Upstream:** Host DNS (10.0.1.1 → Pi-hole)

### External DNS (Planned)

- **Provider 1:** Cloudflare DNS
  - **Zone:** k8s.n37.ca
  - **API:** Uses cert-manager API token
  - **Purpose:** Public DNS records for external access

- **Provider 2:** UniFi UDR7 (RFC2136)
  - **Zone:** k8s.n37.ca (internal)
  - **Purpose:** Split-horizon DNS for internal access
  - **Status:** Pending RFC2136 TSIG key configuration

### DNS Flow
```
Client Query → Pi-hole (10.0.0.200) →
  ├─ Internal: Returns 10.0.10.10 (MetalLB)
  ├─ External: Cloudflare public records
  └─ Upstream: Cloudflare 1.1.1.1/1.0.0.1
```

---

## TLS/SSL Certificates

- **Provider:** Let's Encrypt
- **ACME Challenge:** DNS-01 (via Cloudflare API)
- **Issuer:** ClusterIssuer (cert-manager)
- **Renewal:** Automatic (60 days before expiry)
- **Storage:** Kubernetes Secrets

### Certificate List

| Domain | Type | Issuer | Valid Until | Used By |
|--------|------|--------|-------------|---------|
| argocd.k8s.n37.ca | TLS | Let's Encrypt | Auto-renew | ArgoCD |
| grafana.k8s.n37.ca | TLS | Let's Encrypt | Auto-renew | Grafana |
| localstack.k8s.n37.ca | TLS | Let's Encrypt | Auto-renew | LocalStack |

---

## Firewall & Security

### Inter-VLAN Routing

- **Default:** VLANs are isolated
- **Allowed Routes:**
  - Kubernetes VLAN (10) → Home VLAN (1): For NAS access
  - All VLANs → Internet via gateway
  - Guest VLAN (99): Isolated, internet-only

### Port Forwarding

- **Status:** Not configured (no public-facing services)
- **Cloudflare Tunnel:** Potential future use for secure public access

### Network Policies (Kubernetes)

- **Status:** Calico CNI supports NetworkPolicies
- **Implementation:** Not yet configured
- **Priority:** TODO item #10 - Define isolation between namespaces

---

## Monitoring & Observability

### Network Monitoring

- **UniFi Metrics:** Collected by UniFi Poller → Prometheus
  - Client connections
  - Bandwidth usage per device
  - PoE power consumption
  - Uplink statistics

- **SNMP Monitoring:**
  - Synology NAS via SNMP exporter
  - Network interface statistics on all nodes via node-exporter

- **Ingress Metrics:**
  - nginx-ingress controller metrics → Prometheus
  - Request rates, latencies, error rates per Ingress

### Service Mesh (Future)

- **Status:** Not deployed
- **Consideration:** Linkerd (lightweight) or Istio
- **Purpose:** Service-to-service encryption, traffic management, observability

---

## Network Performance

### Bandwidth

- **Internet Uplink:** Depends on ISP (document actual speed)
- **Internal Network:** 1 Gbps (switch ports)
- **Pi NIC:** 1 Gbps Ethernet (Raspberry Pi 5)
- **iSCSI Storage:** 1 Gbps (Synology to cluster)

### Latency

- **Pod-to-Pod (same node):** < 1ms (local)
- **Pod-to-Pod (cross-node):** 1-2ms (via Calico overlay)
- **Pod-to-External:** Depends on service location

---

## Troubleshooting

### Common Network Issues

1. **Pod cannot reach external internet:**
   - Check: CoreDNS is running (`kubectl get pods -n kube-system -l k8s-app=kube-dns`)
   - Check: Calico pods running (`kubectl get pods -n kube-system -l k8s-app=calico-node`)
   - Check: Node has default route

2. **LoadBalancer IP not assigned:**
   - Check: MetalLB pods running (`kubectl get pods -n metallb-system`)
   - Check: IP pool has available IPs (`kubectl get ipaddresspool -n metallb-system`)
   - Check: Service type is LoadBalancer

3. **Ingress not accessible:**
   - Check: nginx-ingress controller running
   - Check: Ingress has valid host and TLS certificate
   - Check: DNS resolves to MetalLB IP (10.0.10.10)
   - Check: Firewall not blocking ports 80/443

4. **Cannot ping hostNetwork pods on other nodes:**
   - This is a Calico limitation (see CLAUDE_NOTES.md 2025-12-26 Late Night session)
   - Use pod network IPs instead of node IPs

### Diagnostic Commands

```bash
# Check node network status
kubectl get nodes -o wide

# Check pod network (Calico)
kubectl get pods -n kube-system -l k8s-app=calico-node

# Check MetalLB status
kubectl get pods -n metallb-system
kubectl get ipaddresspool -n metallb-system

# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx

# Test DNS resolution from pod
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup kubernetes.default

# Check service endpoints
kubectl get endpoints <service-name> -n <namespace>
```

---

## Future Enhancements

- [ ] Deploy Pi-hole as primary DNS (LoadBalancer IP 10.0.0.200)
- [ ] Configure External-DNS for automatic DNS record creation
- [ ] Implement NetworkPolicies for namespace isolation
- [ ] Set up VPN for secure remote cluster access (Tailscale or WireGuard)
- [ ] Document actual ISP bandwidth and latency baselines
- [ ] Create network topology diagram
- [ ] Implement egress traffic monitoring
- [ ] Consider IPv6 enablement

---

## References

- **Calico Documentation:** https://docs.tigera.io/calico/latest
- **MetalLB Documentation:** https://metallb.universe.tf/
- **nginx-ingress:** https://kubernetes.github.io/ingress-nginx/
- **UniFi Network:** https://ui.com/
- **Synology NAS:** 10.0.1.204 (DSM interface)

---

**Last Updated:** 2025-12-27
**Maintained By:** Claude Code (see CLAUDE_NOTES.md for change history)
