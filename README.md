# Homelab Kubernetes Infrastructure

[![Kubernetes](https://img.shields.io/badge/Kubernetes-v1.35-blue.svg)](https://kubernetes.io/)
[![ArgoCD](https://img.shields.io/badge/GitOps-ArgoCD-orange.svg)](https://argoproj.github.io/argo-cd/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-red.svg)](https://www.raspberrypi.com/products/raspberry-pi-5/)

## Overview

This repository contains the complete infrastructure-as-code for a production-ready Kubernetes homelab cluster running on 5x Raspberry Pi 5 nodes. The cluster implements modern DevOps practices including GitOps with ArgoCD, comprehensive monitoring, centralized logging, and automated backup strategies.

**Documentation Site:** [https://imcbeth.github.io/k8s-docs-n37/](https://imcbeth.github.io/k8s-docs-n37/)

## Quick Start

### Prerequisites
- Kubernetes cluster (v1.35+)
- ArgoCD deployed
- git-crypt configured for secrets management

### Bootstrap Applications
```bash
# Deploy ArgoCD application of applications
kubectl apply -f manifests/applications/
```

## Cluster Architecture

### Hardware Specifications
- **Compute:** 5x Raspberry Pi 5 (16GB RAM each)
- **Storage:** 5x 256GB NVMe SSDs + Synology NAS (iSCSI)
- **Networking:** UniFi Dream Router + USW-Pro-24-POE switch
- **Power:** PoE+ powered with active cooling

### Core Infrastructure
- **Container Runtime:** containerd
- **CNI:** Calico via Tigera Operator (ArgoCD-managed, IPIP encapsulation)
- **Service Mesh:** Istio Ambient (mTLS for 29 pods across 6 namespaces)
- **GitOps:** ArgoCD managing 25 applications
- **Monitoring:** Prometheus + Grafana + AlertManager
- **Logging:** Loki + Alloy with 7-day retention
- **Security:** Trivy Operator (vulnerability scanning) + Falco (runtime security)
- **Backup:** Velero with Backblaze B2 for PVC backups
- **DNS:** External-DNS with Cloudflare + UniFi providers

### Network Architecture
- **Kubernetes VLAN:** 10.0.10.0/24 (cluster nodes)
- **Home VLAN:** 10.0.1.0/24 (NAS, gateway)
- **IoT VLAN:** 10.0.2.0/24 (isolated devices)
- **Work VLAN:** 10.0.100.0/24 (secure workloads)

### Storage Infrastructure
- **Synology CSI Driver:** iSCSI integration for persistent volumes
- **Storage Classes:** `synology-iscsi-retain` for critical data
- **Backup Strategy:** Velero + CSI snapshots to Backblaze B2
- **Data Retention:** Monitoring (50Gi), Logs (20Gi), Grafana (5Gi)

## Directory Structure

### Application Manifests
- **[`manifests/applications/`](manifests/applications/)** - ArgoCD Application definitions
  - Core infrastructure applications (ArgoCD, Prometheus, Grafana)
  - Monitoring tools (Blackbox Exporter, SNMP Exporter, UniFi Poller)
  - Utility applications (External-DNS, Cert-Manager, OPA Gatekeeper, VPA)
  - Backup and storage (Velero, Synology CSI)

- **[`manifests/base/`](manifests/base/)** - Helm charts and Kustomizations
  - Application-specific `values.yaml` configurations
  - Custom resource definitions and policies
  - ConfigMaps and service configurations

### Secrets Management
- **[`secrets/`](secrets/)** - git-crypt encrypted sensitive data
  - **[`README.md`](secrets/README.md)** - Secrets management documentation
  - SMTP credentials for AlertManager
  - API tokens for external services
  - TLS certificates and private keys

### Custom Applications
- **[`apps/DockerFiles/`](apps/DockerFiles/)** - Custom ARM64 container builds
  - **[`README.md`](apps/DockerFiles/README.md)** - Container build documentation

### Automation Scripts
- **[`scripts/`](scripts/)** - Cluster automation and validation
  - **[`validate-manifests.sh`](scripts/validate-manifests.sh)** - Kubernetes manifest validation

## Key Documentation Files

### Architecture Documentation
- **[.claude/CODEMAPS/INDEX.md](.claude/CODEMAPS/INDEX.md)** - Architecture overview and codemap index
- **[.claude/CODEMAPS/networking.md](.claude/CODEMAPS/networking.md)** - CNI, service mesh, network policies
- **[.claude/CODEMAPS/security.md](.claude/CODEMAPS/security.md)** - Trivy, Falco, security monitoring

### Project Management
- **[TODO.md](TODO.md)** - Project roadmap and completion tracking
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development setup and contribution guidelines
- **[CODEOWNERS](CODEOWNERS)** - Code review assignments

### Infrastructure Documentation
- **[Hardware.md](Hardware.md)** - Detailed hardware specifications and procurement guide
- **[network-info.md](network-info.md)** - Network architecture, VLANs, and IP addressing
- **[Install_of_kubernetes.md](Install_of_kubernetes.md)** - Cluster installation procedures

### Configuration References
- **[kube-prometheus-stack.yaml](kube-prometheus-stack.yaml)** - Monitoring stack configuration
- **[Synology_Dashboard.json](Synology_Dashboard.json)** - NAS monitoring dashboard
- **[Synology_Dashboard2.json](Synology_Dashboard2.json)** - Enhanced NAS dashboard

## Project Completion Status

**Overall Progress: ~90% Complete**

Based on the [TODO.md](TODO.md) roadmap:
- **Recently Completed (March–April 2026):**
  - VPA (Vertical Pod Autoscaler) deployed with 7 VPA objects in Off mode
  - Monthly DR validation workflow (Argo Workflows CronWorkflow, tested and validated)
  - Loki log-based alerting via embedded ruler (9 LogQL rules)
  - Ingress-nginx hardened: security headers, rate limiting, Helm migration
  - OPA Gatekeeper in deny mode (5 policies, 0 violations)
  - Calico APIServer deployed for v3 API management
  - Promtail replaced by Alloy (PR #489, 2026-03-01)
  - Renovate automated updates running continuously

- **Completed (January–February 2026):**
  - Tigera Operator migration (Calico CNI now ArgoCD-managed)
  - Istio Ambient mesh (mTLS across 6 namespaces)
  - Falco runtime security + OPA Gatekeeper policy enforcement
  - Trivy Operator vulnerability scanning with compliance reporting
  - Network policies for all 18 namespaces
  - Argo Workflows CI/CD platform
  - Sealed Secrets migration, SealedSecrets key rotation (30d)
  - Resource right-sizing audit (+928Mi optimized)

- **Completed (December 2025):**
  - SNMP monitoring for Synology NAS
  - Log aggregation with Loki + Alloy
  - External-DNS dual provider setup
  - Blackbox Exporter endpoint monitoring
  - Custom Grafana dashboards (30 total)
  - AlertManager SMTP email notifications

### Remaining Work
1. **Observability Maturity** - Distributed tracing (Jaeger/Tempo), SLOs
2. **VPN / Remote Access** - Tailscale or WireGuard
3. **Chaos Engineering** - Litmus for resilience testing
4. **Additional Applications** - Harbor registry, Home Assistant

## Related Repositories

- **[k8s-docs-n37](https://github.com/imcbeth/k8s-docs-n37)** - Comprehensive Docusaurus documentation site
- **[unifi-tf-generator](https://github.com/imcbeth/unifi-tf-generator)** - Terraform configuration generator for UniFi networks

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development environment setup
- Pre-commit hooks and validation
- Git-crypt configuration
- Manifest testing procedures
- Pull request workflow

## Support

For issues and troubleshooting:
1. Check the [Documentation Site](https://imcbeth.github.io/k8s-docs-n37/)
2. Review [.claude/notes/REFERENCE.md](.claude/notes/REFERENCE.md) for common gotchas and solutions
3. Validate manifests with `scripts/validate-manifests.sh`
