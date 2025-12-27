# Contributing to Homelab Infrastructure

Thank you for contributing to the homelab Kubernetes infrastructure!

## Prerequisites

- Kubernetes v1.35.x (for testing)
- kubectl configured with cluster access
- Helm 3.x
- ArgoCD CLI (optional)
- Python 3.x (for pre-commit hooks)
- kubeconform (for Kubernetes manifest validation)
- Git with git-crypt configured

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/imcbeth/homelab.git
cd homelab
```

### 2. Install Development Tools

**macOS:**
```bash
# Pre-commit framework
brew install pre-commit

# Kubernetes manifest validation
brew install kubeconform

# YAML tools
brew install yamllint
```

**Linux:**
```bash
# Pre-commit framework
pip install pre-commit

# Kubeconform
wget https://github.com/yannh/kubeconform/releases/latest/download/kubeconform-linux-amd64.tar.gz
tar xf kubeconform-linux-amd64.tar.gz
sudo mv kubeconform /usr/local/bin/
```

### 3. Install Pre-commit Hooks

```bash
pre-commit install
```

### 4. Test Pre-commit Hooks

```bash
pre-commit run --all-files
```

## Development Workflow

### 1. Create a Branch

Use conventional branch naming:

```bash
git checkout -b feature/deploy-new-app
# or
git checkout -b fix/broken-argocd-sync
# or
git checkout -b docs/update-readme
```

### 2. Make Your Changes

**Infrastructure Changes:**
- Edit manifests in `manifests/base/<application>/`
- Update ArgoCD Application in `manifests/applications/<app>.yaml`
- Set appropriate sync-wave annotations
- Define resource limits for Pi cluster

**Documentation Changes:**
- Update README.md, TODO.md, or CLAUDE_NOTES.md
- Keep documentation in sync with actual deployments

### 3. Validate Locally

**Test Kubernetes Manifests:**
```bash
# Validate with kubeconform
kubeconform -summary manifests/base/<app>/

# Check YAML syntax
yamllint manifests/

# Dry-run with kubectl (requires cluster access)
kubectl apply --dry-run=client -f manifests/base/<app>/
```

**Test Helm Charts:**
```bash
helm template <release-name> <chart> -f manifests/base/<app>/values.yaml
```

### 4. Commit Your Changes

Pre-commit hooks will automatically run:

```bash
git add .
git commit -m "feat: Add new application deployment"
```

**What the hooks check:**
- ✅ Kubernetes manifest validation (kubeconform)
- ✅ YAML syntax and linting
- ✅ Secret scanning (gitleaks)
- ✅ Private key detection
- ✅ Markdown linting
- ✅ Trailing whitespace removal
- ✅ TODO/FIXME detection (warning)

**If hooks fail:**
1. Review the error messages
2. Fix the reported issues
3. Stage fixes: `git add .`
4. Retry: `git commit -m "..."`

### 5. Push and Create PR

```bash
git push -u origin feature/your-feature
gh pr create --title "feat: Your feature" --body "Description..."
```

## GitOps Workflow

### Important Notes

- ⚠️ **Never direct kubectl apply** in production
- ✅ **Always use GitOps** - commit to repo, let ArgoCD sync
- 🔒 **Secrets** - Encrypted with git-crypt, managed separately
- 📝 **Document everything** - Update CLAUDE_NOTES.md with session details

### Deployment Process

1. **Create/update manifests** in `manifests/base/<app>/`
2. **Create ArgoCD Application** in `manifests/applications/<app>.yaml`
3. **Set sync-wave** annotation for deployment order
4. **Create PR** with changes
5. **Review and merge** to main
6. **ArgoCD auto-syncs** within ~3 minutes

### Sync Waves

Critical for proper startup sequence:

```
-50: ArgoCD (self-management)
-35: MetalLB, Pi-hole (networking)
-30: Synology CSI (storage)
-20: UniFi Poller (metrics)
-15: kube-prometheus-stack (monitoring)
-12: Loki (log aggregation)
-11: Promtail (log collection)
-10: cert-manager, external-dns (certificates, DNS)
  0: Applications (default)
```

## Commit Message Format

Use conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New application or feature
- `fix:` - Bug fix or correction
- `update:` - Update existing configuration
- `docs:` - Documentation only
- `chore:` - Maintenance, dependencies

**Examples:**
```
feat(loki): Deploy Loki + Promtail for log aggregation
fix(prometheus): Disable hostNetwork for node-exporter
update(cert-manager): Upgrade to v1.16.3
docs: Add comprehensive network-info.md
```

## Pre-commit Hook Details

### Hooks Configured

1. **Trailing Whitespace** - Removes trailing spaces
2. **End of File Fixer** - Ensures newline at EOF
3. **YAML Syntax Check** - Basic YAML validation
4. **Large File Check** - Prevents files > 1MB
5. **Merge Conflict Check** - Detects unresolved conflicts
6. **Private Key Detection** - Prevents committing keys
7. **YAML Linting** - Advanced YAML validation
8. **Kubeconform** - **Validates Kubernetes manifests!**
9. **Gitleaks** - **Secret scanning**
10. **Markdown Linting** - Enforces markdown style
11. **TODO/FIXME Check** - Warns about markers

### Bypassing Hooks (Not Recommended)

```bash
git commit --no-verify -m "emergency fix"
```

**⚠️ Only use for emergencies!** Bypassing hooks can lead to failed deployments.

### Updating Hooks

```bash
pre-commit autoupdate
```

## Troubleshooting

### Kubeconform Fails

**Problem:** Manifest validation fails

**Solution:**
```bash
# Run manually to see the same validation as the pre-commit hook
kubeconform -summary -output json -ignore-missing-schemas manifests/base/<app>/*.yaml

# Common issues:
# - Invalid API version: Check Kubernetes version compatibility
# - Missing required fields: Add required spec fields
# - Invalid resource type: Verify Kind is correct
```

### YAML Linting Fails

**Problem:** yamllint reports errors

**Solution:**
```bash
# Run manually
yamllint manifests/

# Auto-fix some issues
# (manual fixes required for structure issues)
```

### Gitleaks Detects Secrets

**Problem:** Secret scanning finds potential secrets

**Solution:**
1. **Verify it's not a real secret** - Check the content
2. **If real secret:**
   - Remove it from commit
   - Move to `secrets/` directory (git-crypt encrypted)
   - Use Kubernetes Secret instead
3. **If false positive:**
   - Add pattern to `.gitleaksignore`

### Pre-commit Not Running

**Solution:**
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Check installation
pre-commit --version
git config --get core.hooksPath
```

## Repository Structure

```
homelab/
├── manifests/
│   ├── applications/           # ArgoCD Application CRDs
│   │   ├── argocd.yaml        # Sync-wave: -50
│   │   ├── metal-lb.yaml      # Sync-wave: -35
│   │   ├── cert-manager.yaml  # Sync-wave: -10
│   │   └── ...
│   └── base/                   # Kustomize/Helm bases
│       ├── argocd/
│       ├── cert-manager/
│       ├── loki/
│       └── ...
├── secrets/                    # git-crypt encrypted
├── apps/DockerFiles/           # Custom ARM64 builds
├── docs/                       # Documentation
├── README.md
├── TODO.md
├── Hardware.md
├── network-info.md
└── CLAUDE_NOTES.md            # Session history
```

## Resource Limits Best Practices

Always define resource requests and limits for the Pi cluster:

```yaml
resources:
  requests:
    cpu: 100m        # Guaranteed
    memory: 256Mi
  limits:
    cpu: 200m        # Maximum
    memory: 512Mi
```

**Sizing Guidelines:**
- Lightweight: 100m CPU, 256Mi memory
- Medium: 500m CPU, 512Mi memory
- Heavy: 1000m CPU, 1Gi memory

**Total Available:**
- CPU: 20 cores (5x Pi 5 @ 4 cores)
- Memory: 80GB (5x Pi 5 @ 16GB)

## Testing Changes

### Local Validation

```bash
# Validate manifests
kubeconform -summary -output json -ignore-missing-schemas manifests/base/<app>/*.yaml

# Test Helm template
helm template test <chart> -f manifests/base/<app>/values.yaml

# Dry-run apply
kubectl apply --dry-run=client -f manifests/base/<app>/

# Check ArgoCD diff (without applying)
kubectl apply -f manifests/applications/<app>.yaml
argocd app diff <app-name> --grpc-web
```

### Deployment Testing

1. **Apply to cluster** (via ArgoCD)
2. **Monitor sync status**
   ```bash
   kubectl get application <app> -n argocd -w
   argocd app get <app> --grpc-web
   ```
3. **Check pod status**
   ```bash
   kubectl get pods -n <namespace> -w
   ```
4. **View logs**
   ```bash
   kubectl logs -n <namespace> <pod-name> -f
   ```

## Questions?

- **Issues:** https://github.com/imcbeth/homelab/issues
- **Documentation:** See k8s-docs-n37 repository
- **Session Notes:** CLAUDE_NOTES.md

---

**Happy Infrastructure Coding! 🚀**
