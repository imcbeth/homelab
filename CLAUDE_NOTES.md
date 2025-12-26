# Claude Code - Homelab Repository Guide

## Quick Reference for AI Assistants Working in This Repository

**Last Updated:** 2025-12-26
**Repository:** imcbeth/homelab
**Cluster:** 5x Raspberry Pi 5 (16GB each) Kubernetes Homelab

---

## 📋 Recent Updates

### 2025-12-26: Documentation Site Fixes and SNMP Documentation

**Completed Work:**
- ✅ Fixed broken documentation links preventing Docusaurus deployment
- ✅ Created comprehensive documentation for recently deployed infrastructure
- ✅ Added SNMP exporter documentation for Synology NAS monitoring

**Files Created in k8s-docs-n37:**
- `docs/applications/argocd.md` - Complete ArgoCD GitOps workflow guide
- `docs/applications/snmp-exporter.md` - SNMP exporter for NAS monitoring
- `docs/storage/synology-csi.md` - Synology CSI storage driver documentation
- `docs/troubleshooting/monitoring.md` - Monitoring stack troubleshooting guide

**Files Updated:**
- `docs/monitoring/overview.md` - Added SNMP exporter integration

**Pull Request:** [#3](https://github.com/imcbeth/k8s-docs-n37/pull/3) - Fix broken documentation links

**Build Status:** ✅ Documentation builds successfully without errors

**Key Additions:**
- SNMP exporter monitors Synology DS1522+ NAS (10.0.1.204)
- SNMPv3 authentication with encrypted credentials
- Comprehensive metrics: disk health, volume capacity, RAID status, iSCSI stats
- Grafana dashboard included (Synology_Dashboard2.json)

---

## 🔑 Access & Permissions

### Cluster Access: ✅ AVAILABLE

You have **full access** to the Kubernetes cluster and can execute commands without user approval for:

- **kubectl**: All `get`, `describe`, `delete`, `apply`, `exec` commands
- **helm**: `list`, `uninstall` commands
- **argocd**: All ArgoCD CLI commands
- **gh**: GitHub CLI for PRs, issues, and repository management
- **git**: Full git operations (commit, push via PR workflow)

### Authentication Status

```bash
# Verify cluster access
kubectl cluster-info
# Expected: Kubernetes control plane is running at https://10.0.10.214:6443

# Check ArgoCD access
kubectl get applications -n argocd
# Expected: List of all ArgoCD applications

# Verify GitHub CLI
gh auth status
# Expected: Logged in as imcbeth
```

---

## 🏗️ Infrastructure Overview

### Cluster Details

- **Platform:** Kubernetes v1.35
- **Nodes:** 5x Raspberry Pi 5 (16GB RAM, 256GB NVMe each)
- **Total Resources:** 80GB RAM, 1.28TB NVMe storage
- **CNI:** Calico v3.31.3
- **Ingress:** nginx-ingress v1.14.1
- **Container Runtime:** containerd v2.2.1

### Network Configuration

- **Cluster API:** 10.0.10.214:6443
- **MetalLB IP Pool:** 10.0.10.10 - 10.0.10.99 (90 IPs)
- **Pi-hole DNS:** 10.0.0.200
- **Synology NAS:** 10.0.1.204 (iSCSI storage)
- **UniFi Controller:** 10.0.1.1

### Storage Classes

```yaml
synology-iscsi-retain        # Default, btrfs, /volume2, retains PVs
synology-iscsi-delete        # btrfs, /volume2, deletes PVs
synology-iscsi-retain-ssd    # btrfs, /volume4 (SSD), retains PVs
synology-iscsi-delete-ssd    # btrfs, /volume4 (SSD), deletes PVs
```

---

## 📁 Repository Structure

```
homelab/
├── manifests/
│   ├── applications/           # ArgoCD Application definitions
│   │   ├── argocd.yaml                    # Sync-wave: -50
│   │   ├── metal-lb.yaml                  # Sync-wave: -35
│   │   ├── synology-csi.yaml              # Sync-wave: -30
│   │   ├── unipoller.yaml                 # Sync-wave: -20
│   │   ├── kube-prometheus-stack.yaml     # Sync-wave: -15
│   │   ├── cert-manager.yaml              # Sync-wave: -10
│   │   ├── pi-hole.yaml                   # Sync-wave: -35
│   │   └── localstack.yaml                # Sync-wave: 0
│   │
│   └── base/                   # Kustomize/Helm configuration bases
│       ├── argocd/
│       ├── cert-manager/
│       ├── metal-lb/
│       ├── pihole/
│       ├── localstack/
│       ├── synology-csi/
│       ├── unipoller/
│       └── kube-prometheus-stack/
│
├── secrets/                    # git-crypt encrypted secrets
│   └── argocd-git-access.yaml
│
├── apps/DockerFiles/           # Custom ARM64 container builds
├── docs/                       # Documentation
├── README.md
├── TODO.md                     # Active roadmap
├── Hardware.md
├── Install_of_kubernetes.md
└── CLAUDE_NOTES.md            # This file
```

---

## 🚀 GitOps Workflow

### Branch Protection

⚠️ **IMPORTANT:** The `main` branch has protection rules requiring pull requests.

**Workflow:**
1. Create feature branch: `git checkout -b feature-name`
2. Make changes and commit
3. Push branch: `git push -u origin feature-name`
4. Create PR: `gh pr create --title "..." --body "..." --base main`
5. Merge PR: `gh pr merge <number> --squash --admin`

### ArgoCD Auto-Sync

All applications have **automated sync** enabled with:
- `prune: true` - Remove resources not in git
- `selfHeal: true` - Revert manual changes
- `CreateNamespace: true` - Auto-create namespaces

**After merging to main:** ArgoCD will automatically deploy changes within ~3 minutes.

**Manual sync if needed:**
```bash
# Sync specific application
argocd app sync <app-name> --grpc-web

# Or apply Application manifest directly
kubectl apply -f manifests/applications/<app-name>.yaml
```

---

## 🔐 Secrets Management

### Current State: git-crypt

Secrets are encrypted using **git-crypt** with pattern matching in `.gitattributes`:

```gitattributes
*.key filter=git-crypt diff=git-crypt
*secret* filter=git-crypt diff=git-crypt
secrets/** filter=git-crypt diff=git-crypt
```

### ⚠️ Known Limitation

**ArgoCD cannot decrypt git-crypt encrypted secrets automatically.**

When deploying applications with secrets:
1. Secrets will show as encrypted binary in ArgoCD
2. You may need to manually apply: `kubectl apply -f manifests/base/<app>/secret.yaml`
3. This is a temporary workaround

### Future Enhancement (TODO)

Implement one of these from the TODO list:
- External Secrets Operator (recommended)
- Sealed Secrets
- ArgoCD Vault Plugin

---

## 📊 Deployed Applications

| Application | Namespace | Purpose | Sync Wave | Status |
|------------|-----------|---------|-----------|--------|
| argocd | argocd | GitOps controller | -50 | Self-managed |
| metal-lb | metallb-system | Load balancer | -35 | Layer 2, IP pool |
| pi-hole | pihole | DNS/DHCP | -35 | 10.0.0.200 |
| synology-csi | synology-csi | Storage driver | -30 | iSCSI to NAS |
| unipoller | unipoller | UniFi metrics | -20 | Scrapes 10.0.1.1 |
| kube-prometheus-stack | default | Monitoring | -15 | Prometheus/Grafana/AlertManager |
| snmp-exporter | default | NAS monitoring | -15 | SNMPv3 to 10.0.1.204 |
| cert-manager | cert-manager | TLS certs | -10 | Let's Encrypt via Cloudflare |
| localstack | localstack | AWS mock | 0 | Dev/testing |

---

## 🛠️ Common Operations

### Check Application Health

```bash
# All applications
kubectl get applications -n argocd

# Specific application with details
kubectl get application <name> -n argocd -o yaml

# Application pods
kubectl get pods -n <namespace>

# Application sync status
argocd app get <name> --grpc-web
```

### Deploy New Application

1. Create base manifests in `manifests/base/<app-name>/`
2. Create Application in `manifests/applications/<app-name>.yaml`
3. Set appropriate sync-wave annotation
4. Choose project: `infrastructure` (preferred) or `applications`
5. Commit, create PR, merge
6. ArgoCD will auto-deploy

### Update Existing Application

1. Edit files in `manifests/base/<app-name>/`
2. Commit, create PR, merge
3. ArgoCD auto-syncs within ~3 minutes

### Debug Pod Issues

```bash
# Describe pod
kubectl describe pod <pod-name> -n <namespace>

# View logs
kubectl logs <pod-name> -n <namespace>

# Exec into pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Check events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### Helm Operations

```bash
# List all Helm releases (should be minimal, most are ArgoCD-managed)
helm list -A

# If you need to uninstall before ArgoCD takeover
helm uninstall <release-name> -n <namespace>
```

### Resource Limits Best Practices

For Raspberry Pi cluster, always add resource limits:

```yaml
resources:
  requests:
    cpu: 100m        # Guaranteed CPU
    memory: 256Mi    # Guaranteed memory
  limits:
    cpu: 200m        # Maximum CPU
    memory: 512Mi    # Maximum memory
```

**Sizing Guidelines:**
- Lightweight services: 100m CPU, 256Mi memory
- Medium services: 500m CPU, 512Mi memory
- Heavy services: 1000m CPU, 1Gi memory

---

## 🎯 Deployment Order (Sync Waves)

Critical for proper startup sequence:

```
-50: ArgoCD (self-management, must be first)
-35: MetalLB, Pi-hole (networking layer)
-30: Synology CSI (storage layer)
-20: UniFi Poller (metrics collection)
-15: kube-prometheus-stack (monitoring stack)
-10: cert-manager (TLS certificate management)
  0: Application layer (LocalStack, etc.)
```

**Why this matters:**
- Applications requiring LoadBalancer IPs need MetalLB running
- Applications needing PVCs need Synology CSI running
- TLS-enabled ingresses need cert-manager running

---

## 📝 Commit Message Format

Use this format for commits:

```
<Type>: <Short description>

<Detailed explanation of changes>
- Bullet point 1
- Bullet point 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types:** feat, fix, update, refactor, docs, chore

---

## 🔍 Monitoring & Observability

### Access Points

- **Grafana:** `https://grafana.k8s.n37.ca` (via kube-prometheus-stack)
- **Prometheus:** `http://kube-prometheus-stack-prometheus.default:9090`
- **ArgoCD:** `https://argocd.k8s.n37.ca`
- **Pi-hole:** `https://pihole.k8s.n37.ca`
- **LocalStack:** `https://localstack.k8s.n37.ca`

### Prometheus Scrape Targets

```yaml
# UniFi Poller (network metrics)
- job_name: 'unpoller'
  targets: ['unifi-poller.unipoller:9130']

# SNMP Exporter (Synology NAS monitoring)
- job_name: 'snmp-nas'
  targets: ['10.0.1.204']  # Synology DS1522+
  metrics_path: /snmp
  params:
    module: [synology]
  relabel_configs:
    - target_label: __address__
      replacement: snmp-exporter.default:9116

# All K8s nodes (via node-exporter DaemonSet)
# All K8s services (via kube-state-metrics)
# etcd, API server, controller-manager, scheduler
```

### Important PVCs

```bash
# Prometheus data (50Gi) - CRITICAL, contains all metrics history
prometheus-kube-prometheus-stack-prometheus-db-prometheus-kube-prometheus-stack-prometheus-0

# Pi-hole data
# Check: kubectl get pvc -n pihole
```

---

## ⚠️ Important Notes

### UniFi Controller TLS

The UniFi controller at 10.0.1.1 **does not have a valid certificate**.
Setting: `UP_UNIFI_CONTROLLER_0_VERIFY_SSL: "false"` is **intentional** and documented.
**Do not** flag this as a security issue in future reviews.

### Container Image Versions

All container images should be **pinned to specific versions**, never `latest`.

**Current pinned versions:**
- unpoller: `v2.11.2`
- localstack: `3.9.0`
- kube-prometheus-stack: `80.6.0`

### Node Labels

Check if any workload-specific node labels exist:
```bash
kubectl get nodes --show-labels
```

---

## 🐛 Known Issues & Workarounds

### 1. Git-Crypt Secrets + ArgoCD

**Issue:** ArgoCD cannot decrypt git-crypt secrets
**Workaround:** Manually apply secrets: `kubectl apply -f manifests/base/<app>/secret.yaml`
**Long-term fix:** Implement External Secrets Operator (on TODO list)

### 2. Prometheus Storage

**Status:** ✅ RESOLVED
50Gi PVC configured at `kube-prometheus-stack.yaml` line 1376

---

## 📚 Additional Resources

- **TODO.md** - Active roadmap with 17 task groups
- **Hardware.md** - Detailed hardware specifications
- **Install_of_kubernetes.md** - Cluster setup procedures
- **README.md** - Project overview

---

## 🔄 When Working on New Features

### Pre-Implementation Checklist

- [ ] Read TODO.md for alignment with roadmap
- [ ] Check existing patterns in similar applications
- [ ] Determine appropriate sync-wave
- [ ] Plan resource limits for Pi cluster constraints
- [ ] Consider storage requirements (PVC sizing)
- [ ] Identify secret management needs
- [ ] Check if TLS/Ingress needed

### Post-Implementation Checklist

- [ ] Add resource limits (CPU/memory)
- [ ] Pin container image versions (no `latest`)
- [ ] Set sync-wave annotation
- [ ] Configure automated sync policy
- [ ] Test deployment in cluster
- [ ] Verify health status in ArgoCD
- [ ] Update this document if needed
- [ ] Document in README.md if significant

---

## 🆘 Emergency Procedures

### Application Won't Sync

```bash
# Check sync status
kubectl get application <name> -n argocd -o yaml | grep -A 20 "status:"

# Force refresh
argocd app get <name> --refresh --grpc-web

# Force sync (bypass policies)
argocd app sync <name> --force --grpc-web
```

### Pod CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n <namespace> --previous

# Check events
kubectl describe pod <pod-name> -n <namespace>

# Common fixes:
# - Verify ConfigMap/Secret exists
# - Check resource limits
# - Verify image pull successful
# - Check persistent storage
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -A

# Check PV status
kubectl get pv

# Synology CSI driver
kubectl get pods -n synology-csi
kubectl logs -n synology-csi <csi-pod-name>
```

### Cluster Unresponsive

```bash
# Check node status
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system

# Check control plane
kubectl cluster-info dump
```

---

## 💡 Tips for Efficiency

1. **Use Tab Completion:** Set up kubectl/argocd completions
2. **Aliases:** Consider setting up common command aliases
3. **Context:** Always verify namespace when running commands
4. **Dry Run:** Use `--dry-run=client` for testing kubectl commands
5. **Watch Mode:** Use `kubectl get <resource> -w` to watch for changes
6. **ArgoCD UI:** Sometimes easier than CLI for complex debugging

---

## 📚 Comprehensive Documentation Site

### Docusaurus Site: ~/k8s-docs-n37

**IMPORTANT:** There is a comprehensive Docusaurus documentation site that provides detailed guides for this cluster.

**Location:** `/Users/imcbeth/k8s-docs-n37`

**When to Update the Docs Site:**
- ✅ After deploying new applications → Create/update docs in `docs/applications/`
- ✅ After infrastructure changes → Update relevant sections
- ✅ After monitoring stack updates → Update `docs/monitoring/`
- ✅ After adding/modifying storage → Update `docs/storage/`

**Documentation Structure:**
```
k8s-docs-n37/docs/
├── intro.md                    # Main landing page
├── getting-started/
│   ├── hardware.md
│   ├── overview.md
│   └── prerequisites.md
├── kubernetes/
│   ├── installation.md
│   └── cluster-configuration.md
├── applications/              # Application deployment guides
├── monitoring/                # Monitoring stack documentation
│   └── overview.md
├── storage/                   # Storage documentation
├── security/                  # Security documentation
└── troubleshooting/           # Common issues and solutions
```

**Workflow:**
1. Make infrastructure changes in `homelab/` repo
2. Update documentation in `k8s-docs-n37/` repo
3. Keep both repositories in sync
4. The docs site provides user-friendly guides while `homelab/` is the source of truth for configs

---

## 📞 Getting Help

- **GitHub Issues:** https://github.com/imcbeth/homelab/issues
- **ArgoCD Docs:** https://argo-cd.readthedocs.io/
- **Kubernetes Docs:** https://kubernetes.io/docs/
- **Repository Owner:** @imcbeth
- **Comprehensive Docs:** `/Users/imcbeth/k8s-docs-n37` (Docusaurus site)

---

**Remember:** This is a **production homelab** with active services. Always test changes in a branch and use the PR workflow. ArgoCD will auto-deploy merged changes, so review carefully before merging. When making significant changes, update both the infrastructure repo (`homelab/`) and the documentation site (`k8s-docs-n37/`).

---

**Remember:** This is a **production homelab** with active services. Always test changes in a branch and use the PR workflow. ArgoCD will auto-deploy merged changes, so review carefully before merging.
