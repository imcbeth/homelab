# 2026-01-30: Tigera Operator Migration and ArgoCD Sync Patterns

**Context:** Major infrastructure migration to move Calico CNI from manifest-based installation (kube-system) to Tigera operator-managed (calico-system). This session documents the architectural changes and ArgoCD sync patterns established.

## Completed Work

### Tigera Operator Migration (PRs #345-352)

Migrated Calico CNI from static manifests to GitOps-managed Tigera operator. This enables version-controlled CNI configuration and automated reconciliation.

**Architecture Change:**
```
Before: Calico manifests in kube-system (manual kubectl apply)
After:  Tigera operator in tigera-operator namespace (ArgoCD-managed)
        Calico components in calico-system namespace (operator-managed)
```

**Pull Requests:**
- **PR #345:** fix: Add control-plane toleration for Trivy node-collector
  - Enables vulnerability scanning of control-plane nodes

- **PR #346:** feat: Add Tigera operator managed via ArgoCD
  - Multi-source Application: operator from GitHub, Installation CR from homelab repo
  - Sync wave -100 (deploys before all other applications)
  - Installation CR preserves existing config (192.168.0.0/16 CIDR, IPIP encapsulation)

- **PR #347:** fix: Update Tigera Installation CR for compatibility
  - Removed invalid containerIPForwarding field
  - Added topologySpreadConstraints for Typha (distribute across all nodes)

- **PR #348:** fix: Ignore operator-managed fields in Tigera Installation CR
  - Added ignoreDifferences for fields operator mutates at runtime

- **PR #349:** fix: Ignore CRD preserveUnknownFields in Tigera app
  - CRDs have runtime fields that differ from upstream

- **PR #350:** fix: Resolve ArgoCD sync and resource issues
  - Increased argocd-repo-server memory: 256Mi -> 512Mi
  - Root cause: OOMKilled (13 restarts) from large manifest generation
  - Tigera operator and kube-prometheus-stack spike to 400Mi+
  - Added /spec/registry to ignoreDifferences (operator normalizes trailing slash)

- **PR #351:** fix: Use jqPathExpressions for ignoreDifferences
  - jsonPointers weren't correctly matching nested fields
  - jqPathExpressions provide more reliable field selection

- **PR #352:** fix: Add RespectIgnoreDifferences to kube-prometheus-stack
  - Enables ignoreDifferences during automated sync
  - Prevents perpetual OutOfSync from Grafana password regeneration

### ArgoCD ignoreDifferences Patterns

**Key Learning:** Operator-managed resources require careful ignoreDifferences configuration. The operator mutates fields at runtime that differ from the declared spec.

**Pattern for Tigera Operator:**
```yaml
ignoreDifferences:
  # Installation CR - operator adds defaults
  - group: operator.tigera.io
    kind: Installation
    jsonPointers:
      - /status
      - /spec/cni
      - /spec/flexVolumePath
      - /spec/registry
      - /spec/calicoNetwork/hostPorts
      # ... many more operator-managed fields

  # CRDs - runtime annotations differ from upstream
  - group: apiextensions.k8s.io
    kind: CustomResourceDefinition
    jqPathExpressions:
      - .metadata.annotations
      - .spec.preserveUnknownFields
```

**Pattern for kube-prometheus-stack (Grafana password):**
```yaml
ignoreDifferences:
  # Grafana generates random password each render
  - group: ""
    kind: Secret
    name: kube-prometheus-stack-grafana
    jqPathExpressions:
      - .data["admin-password"]
  - group: apps
    kind: Deployment
    name: kube-prometheus-stack-grafana
    jqPathExpressions:
      - .spec.template.metadata.annotations["checksum/secret"]
```

**Critical syncOption:**
```yaml
syncPolicy:
  syncOptions:
    - RespectIgnoreDifferences=true  # Required for automated sync!
```

### Resource Right-Sizing

**ArgoCD repo-server:**
| Setting | Before | After | Reason |
|---------|--------|-------|--------|
| Memory request | 128Mi | 256Mi | Large manifest spikes |
| Memory limit | 256Mi | 512Mi | Prevent OOMKilled |

## Configuration Files

**Tigera Operator Application:**
- `/Users/imcbeth/homelab/manifests/applications/tigera-operator.yaml`

**Installation CR:**
- `/Users/imcbeth/homelab/manifests/base/tigera-operator/installation.yaml`

Key settings:
- Pod CIDR: 192.168.0.0/16 (matches kubeadm)
- Encapsulation: IPIP
- BGP: Enabled
- Typha: topologySpreadConstraints for node distribution
- Resources: Tuned for Pi cluster

**ArgoCD Config:**
- `/Users/imcbeth/homelab/manifests/base/argocd/argocd-config.yaml`

## Sync Wave Order Update

```
Wave -100: tigera-operator (CNI foundation - NEW)
Wave  -50: argocd (self-management)
Wave  -35: metal-lb, pi-hole (networking)
Wave  -30: synology-csi (storage)
Wave  -25: sealed-secrets (secrets)
Wave  -20: unipoller (metrics)
Wave  -15: kube-prometheus-stack (monitoring)
Wave  -12: loki (logging)
Wave  -11: promtail (log collection)
Wave  -10: cert-manager, external-dns, metrics-server
Wave   -8: argo-workflows (CI/CD)
Wave   -7: localstack (S3 mock)
Wave   -5: velero, falco (backup, security)
```

## Key Technical Learnings

1. **Operator-managed resources need ignoreDifferences:** Operators add defaults and mutate fields that cause perpetual OutOfSync without proper ignore configuration.

2. **jqPathExpressions > jsonPointers:** jqPathExpressions are more reliable for complex field paths and work better with nested structures.

3. **RespectIgnoreDifferences is required for automated sync:** Without this syncOption, ignoreDifferences only applies to manual syncs.

4. **Large manifests need memory:** repo-server must have sufficient memory for operators with many CRDs (Tigera, Prometheus).

5. **Typha topology spread:** Running Typha on all nodes prevents connectivity issues when node02/node03 couldn't reach remote Typha.

## Files Modified

**Applications:**
- `manifests/applications/tigera-operator.yaml` (new)
- `manifests/applications/kube-prometheus-stack.yaml`
- `manifests/applications/trivy-operator.yaml`

**Base configs:**
- `manifests/base/tigera-operator/installation.yaml` (new)
- `manifests/base/argocd/argocd-config.yaml`
- `manifests/base/trivy-operator/values.yaml`

## Verification Commands

```bash
# Check Calico status
kubectl get installation default -o yaml

# Verify Typha distribution
kubectl get pods -n calico-system -l k8s-app=calico-typha -o wide

# Check ArgoCD sync status
kubectl get applications -n argocd

# View repo-server resource usage
kubectl top pod -n argocd -l app.kubernetes.io/component=repo-server
```

## Related Documentation

- k8s-docs-n37: Needs update for Tigera operator migration
- TODO.md: Needs Falco marked complete
- README.md: Update CNI description
