### 2026-01-24 (Night): Argo Workflows Deployment

**Completed Work:**
- Deployed Argo Workflows v3.7.8 (Helm chart 0.47.1) at sync-wave -8
- Configured Pi-optimized resource limits (Controller: 100m/256Mi, Server: 50m/128Mi)
- Created SealedSecret for B2 credentials (`homelab-workflows` bucket)
- Added test WorkflowTemplates (hello-world, artifact-test)
- Created NetworkPolicy for argo-workflows namespace (temporarily disabled)
- Test workflow executed successfully

**Pull Requests:**
- **PR #277:** [Merged] feat: Add Argo Workflows for CI/CD pipeline automation
- **PR #280:** [Merged] fix: Set default serviceAccountName for Argo Workflows
- **PR #281:** [Merged] fix: Update Argo Workflows B2 credentials
- **PR #282:** [Merged] fix: Correct NetworkPolicy DNS and API rules
- **PR #283:** [Merged] fix: Temporarily disable argo-workflows NetworkPolicy
- **PR #284:** [Merged] fix: Disable archiveLogs until B2 permissions are fixed
- **PR #285:** [Merged] docs: Mark Argo Workflows as deployed in TODO.md

**Issues Resolved:**
1. **Workflow pods using wrong service account** - Added `serviceAccountName: argo-workflow` to workflowDefaults
2. **NetworkPolicy blocking K8s API** - Fixed in PR #291
3. **B2 "not entitled" error** - Fixed in PRs #287-289

**Files Created:**
- `manifests/applications/argo-workflows.yaml`
- `manifests/base/argo-workflows/values.yaml`
- `manifests/base/argo-workflows/b2-credentials-sealed.yaml`
- `manifests/base/argo-workflows/test-workflow.yaml`
- `manifests/base/network-policies/argo-workflows/network-policy.yaml`

**Final Cluster Status:**
- 16/16 ArgoCD applications Synced and Healthy
- Test workflow: Succeeded

---

### 2026-01-24 (Late Night): Argo Workflows Completion & Ingress

**Completed Work:**
- Verified B2 artifact storage working (ran artifact-test workflow successfully)
- Fixed NetworkPolicy K8s API egress - requires both ClusterIP AND control plane network
- Added nginx ingress for Argo Workflows UI at workflows.k8s.n37.ca
- Updated NetworkPolicies for velero and trivy-system with same API egress fix
- Discovered external-dns-cloudflare not syncing (investigating)

**Pull Requests:**
- **PR #290:** [Merged] docs: Mark Argo Workflows B2 artifact storage as fixed
- **PR #291:** [Merged] fix: Add control plane network to NetworkPolicy API egress rules
- **PR #292:** [Merged] docs: Update session notes - NetworkPolicy fix complete
- **PR #293:** [Merged] feat: Add nginx ingress for Argo Workflows UI

**Key Discovery - NetworkPolicy K8s API Egress:**
With Calico CNI, K8s API access requires BOTH:
1. ClusterIP service: `10.96.0.1/32:443`
2. Control plane network: `10.0.10.0/24:6443`

**Files Created/Modified:**
- `manifests/base/argo-workflows/ingress.yaml` (new)
- `manifests/base/network-policies/argo-workflows/network-policy.yaml` (enabled + fixed)
- `manifests/base/network-policies/velero/network-policy.yaml` (API egress fix)
- `manifests/base/network-policies/trivy-system/network-policy.yaml` (API egress fix)

---

### 2026-01-24 (Evening): Network Policies Implementation

**Completed Work:**
- Implemented Kubernetes NetworkPolicies for 5 namespaces
- Created ArgoCD Application for GitOps deployment (sync-wave -40)
- Validated all policies don't break existing functionality
- All tests passed: Prometheus scraping, Velero backups, Loki logs

**Pull Requests:**
- **PR #274:** [Merged] feat: Add NetworkPolicies for namespace isolation
- **PR #57:** [Merged] docs: Add Network Policies documentation (k8s-docs-n37)

**NetworkPolicies Deployed:**
| Namespace | Ingress Allowed | Egress Allowed |
|-----------|-----------------|----------------|
| localstack | velero, ingress-nginx, prometheus | DNS only |
| unipoller | prometheus | DNS, UniFi (10.0.1.1) |
| loki | promtail, prometheus, grafana | DNS, alertmanager |
| trivy-system | prometheus | DNS, K8s API, registries |
| velero | prometheus | DNS, localstack, B2, K8s API |

**Files Created:**
- `manifests/base/network-policies/kustomization.yaml`
- `manifests/base/network-policies/{localstack,unipoller,loki,trivy-system,velero}/network-policy.yaml`
- `manifests/applications/network-policies.yaml`
