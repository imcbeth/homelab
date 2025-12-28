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
- **CNI:** Calico with VLAN segmentation
- **GitOps:** ArgoCD managing 25+ applications
- **Monitoring:** Prometheus + Grafana + AlertManager
- **Logging:** Loki + Promtail with 7-day retention
- **Backup:** Velero with Kopia for PVC backups
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

### Project Management
- **[TODO.md](TODO.md)** - Project roadmap and completion tracking (~47% complete)
- **[CLAUDE_NOTES.md](CLAUDE_NOTES.md)** - AI assistant session history and troubleshooting guide
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

**Overall Progress: ~73% Complete**

Based on the [TODO.md](TODO.md) roadmap:
- **✅ Recently Completed (December 2025):** 78 major tasks
  - SNMP monitoring for Synology NAS
  - Log aggregation with Loki + Promtail
  - External-DNS dual provider setup
  - Blackbox Exporter endpoint monitoring
  - Metrics Server deployment
  - Custom Grafana dashboards (4 new, 30 total)
  - Log-based alerting with Loki Ruler
  - AlertManager SMTP email notifications
  - Velero backup solution

- **🔄 Currently In Progress:** 15 ongoing initiatives
  - Enhanced alerting (webhook integration)
  - Backup testing and disaster recovery
  - Security scanning implementation
  - Platform enhancements (service mesh evaluation)

- **📋 Planned:** 33 future enhancements
  - Trivy Operator for vulnerability scanning
  - Falco for runtime security
  - Istio/Linkerd service mesh
  - GitOps automation improvements

### High-Priority Next Steps
1. **LocalStack Sync Wave Fix** - Resolve Velero dependency issues
2. **Backup Testing** - Validate disaster recovery procedures
3. **Security Scanning** - Deploy Trivy Operator
4. **Predictive Alerting** - Disk space and performance monitoring

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
