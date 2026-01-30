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
- **GitOps:** ArgoCD managing 27+ applications
- **Monitoring:** Prometheus + Grafana + AlertManager
- **Logging:** Loki + Promtail with 7-day retention
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
- **Backup Strategy:** Velero + Kopia to cloud storage
- **Data Retention:** Monitoring (50Gi), Logs (20Gi), Grafana (5Gi)

## Directory Structure

### Application Manifests
- **[`manifests/applications/`](manifests/applications/)** - ArgoCD Application definitions
  - Core infrastructure applications (ArgoCD, Prometheus, Grafana)
  - Monitoring tools (Blackbox Exporter, SNMP Exporter, UniFi Poller)
  - Utility applications (External-DNS, Cert-Manager, Pi-hole)
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
- **[docs/CODEMAPS/INDEX.md](docs/CODEMAPS/INDEX.md)** - Architecture overview and codemap index
- **[docs/CODEMAPS/networking.md](docs/CODEMAPS/networking.md)** - CNI, service mesh, network policies
- **[docs/CODEMAPS/security.md](docs/CODEMAPS/security.md)** - Trivy, Falco, security monitoring

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

**Overall Progress: ~60% Complete**

Based on the [TODO.md](TODO.md) roadmap:
- **Recently Completed (January 2026):**
  - Tigera Operator migration (Calico CNI now ArgoCD-managed)
  - Istio Ambient mesh (mTLS across 6 namespaces)
  - Falco runtime security monitoring
  - Trivy Operator vulnerability scanning
  - Network policies for all namespaces
  - Argo Workflows CI/CD platform
  - Renovate automated dependency updates
  - Sealed Secrets migration from git-crypt
  - Velero with Backblaze B2 storage

- **Completed (December 2025):**
  - SNMP monitoring for Synology NAS
  - Log aggregation with Loki + Promtail
  - External-DNS dual provider setup
  - Blackbox Exporter endpoint monitoring
  - Metrics Server deployment
  - Custom Grafana dashboards (30 total)
  - AlertManager SMTP email notifications

### High-Priority Next Steps
1. **Observability Maturity** - SLOs, distributed tracing, anomaly detection
2. **Disaster Recovery Testing** - Monthly DR drills, chaos engineering
3. **Resource Optimization** - VPA, right-sizing analysis
4. **Documentation** - Operational runbooks, network topology diagrams

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
2. Review [CLAUDE_NOTES.md](CLAUDE_NOTES.md) for common solutions
3. Validate manifests with `scripts/validate-manifests.sh`
