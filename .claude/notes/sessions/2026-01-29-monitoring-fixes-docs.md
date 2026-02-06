### 2026-01-29 (Morning): Blackbox-Exporter Hairpin NAT Fix

**Completed Work:**
- Diagnosed blackbox-exporter failing to probe internal HTTPS endpoints
- Root cause: DNS resolves to external MetalLB IP (10.0.10.10), causing hairpin NAT timeout
- Fix: Added `hostAliases` to resolve internal hostnames to ingress ClusterIP (10.98.168.24)

**Pull Requests:**
- **PR #327:** [Merged] fix: Add hostAliases to blackbox-exporter for hairpin NAT

**Hostnames Fixed:**
- argocd.k8s.n37.ca, grafana.k8s.n37.ca, workflows.k8s.n37.ca, localstack.k8s.n37.ca

**Files Modified:**
- `manifests/base/kube-prometheus-stack/blackbox-exporter-deployment.yaml`

---

### 2026-01-29 (Afternoon): Documentation Updates

**Completed Work:**
- Updated k8s-docs-n37 documentation with recent fixes
- Added hairpin NAT troubleshooting to blackbox-exporter.md
- Added Promtail selective labelmap section to loki.md
- Expanded Istio ArgoCD OutOfSync fix in istio.md
- Extracted reusable patterns as learned skills

**Pull Requests:**
- **PR #59 (k8s-docs-n37):** docs: Add troubleshooting sections for recent fixes

**Learned Skills Extracted:**
- `~/.claude/skills/learned/kubernetes-hairpin-nat-workaround.md`
- `~/.claude/skills/learned/promtail-loki-label-limit.md`

---

### 2026-01-29 (Evening): Monitoring Fixes & Network Policy Documentation

**Completed Work:**
- Created Argo Workflows Grafana dashboard with ServiceMonitor
- Fixed metrics-server ServiceMonitor (was showing DOWN in Prometheus)
- Fixed Trivy NetworkPolicy blocking vulnerability scans
- Documented network segmentation strategy in k8s-docs-n37

**Pull Requests:**
- **PR #330:** [Merged] feat: Add Argo Workflows Grafana dashboard and enable ServiceMonitor
- **PR #331:** [Merged] fix: Enable metrics-server HTTPS scraping and Trivy intra-namespace communication
- **PR #332:** docs: Mark network policies documentation as complete
- **PR #60 (k8s-docs-n37):** docs: Update NetworkPolicies documentation with current implementation

**Issues Resolved:**
1. **Metrics-Server ServiceMonitor DOWN** - Helm chart doesn't support `scheme: https`; added third ArgoCD source for manual manifests
2. **Trivy Dashboard Empty** - NetworkPolicy blocked intra-namespace communication; added egress/ingress rules

**Files Modified:**
- `manifests/base/argo-workflows/values.yaml` (ServiceMonitor config)
- `manifests/base/grafana/dashboards/argo-workflows-dashboard.yaml` (new)
- `manifests/base/grafana/dashboards/kustomization.yaml`
- `manifests/applications/metrics-server.yaml` (third source)
- `manifests/base/metrics-server/values.yaml` (disable Helm ServiceMonitor)
- `manifests/base/network-policies/trivy-system/network-policy.yaml`
