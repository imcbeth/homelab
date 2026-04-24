### 2026-02-15: Webhook Timeout Fix, Calico-APIServer CPU & Prometheus Alert Fix

Archived from CURRENT.md. See full details in conversation history.

**Key Work:** Fixed ingress-nginx webhook timeout (IPIP/ipBlock issue → bare port rule), calico-apiserver CPU throttling (100m → 250m), broken ExposedSecretsDetected alert (PromQL or → max by). Full cluster log review of 11 components. k8s-docs-n37 sync (PR #67).

**PRs:** #453, #454, #455, k8s-docs-n37 #67
