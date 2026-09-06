# Weekend Runbook — Ubuntu updates + kernel reboot cycle

**Target:** apply pending apt updates + roll each node through a reboot onto the latest available raspi kernel

> **Kernel versions in this runbook go stale fast.** As drafted (2026-07-30) the pending kernel was `6.8.0-1060`. By the 2026-09-06 run it was `6.8.0-1064`. Don't hard-code the expected version — check what `apt-get upgrade` actually installs (`ls /boot/vmlinuz-*`) and confirm `uname -r` matches it after reboot.
>
> **Progress log:**
> - 2026-08 (before 09-06): node02, node04 → `6.8.0-1060`
> - 2026-09-06: control-plane, node01, node03 → `6.8.0-1064`
> - **Outstanding:** node02 + node04 still on `-1060`, need another pass to converge on `-1064`
**Estimated wall time:** ~2 hours across all 5 nodes (with observation windows)
**Drafted:** 2026-07-30
**Do NOT run on:** Wednesday (chaos-mesh fires 09:00-11:00 UTC)

## Baseline state (as of 2026-07-30)

Verified via `ssh` to each node:

| Node | Current kernel | Upgradable packages | Security updates | reboot-required |
|---|---|---|---|---|
| control-plane (10.0.10.214) | 6.8.0-1057-raspi | 65 | 2 | ✅ |
| node01 (10.0.10.235) | 6.8.0-1057-raspi | 65 | 2 | ✅ |
| node02 (10.0.10.211) | 6.8.0-1057-raspi | 65 | 2 | ✅ |
| node03 (10.0.10.244) | 6.8.0-1057-raspi | 65 | 2 | ✅ |
| node04 (10.0.10.220) | 6.8.0-1057-raspi | 65 | 2 | ✅ |

All 5 nodes need reboot for the kernel that's already installed on disk. Rolling one node at a time keeps 4/5 available at all times.

## Prerequisites

- [ ] Cluster in Synced+Healthy steady state (verify via `/cluster-healthcheck`)
- [ ] No open Renovate PRs blocking the window
- [ ] Recent Velero backup within 24h
- [ ] **NOT Wednesday** — chaos-mesh fires 09:00-11:00 UTC would collide
- [ ] Gatekeeper on 2 replicas with hard anti-affinity (PR #845, merged 2026-07-30) so drains don't PDB-block

## Node order

Rolling one at a time — cluster stays available throughout. Control-plane last so we finish with the api-server end.

1. **node04** (10.0.10.220) — least critical PVCs (already handled the messy drain during k8s upgrade)
2. **node03** (10.0.10.244) — has Loki
3. **node02** (10.0.10.211) — has Prometheus
4. **node01** (10.0.10.235) — has Falco Redis
5. **control-plane** (10.0.10.214) — api-server; do LAST

## Per-node procedure

Repeat this block for each node in the order above. Copy-paste the two variables at the top.

```bash
NODE=node04
IP=10.0.10.220

# --- 1. Drain (safely evict everything, respecting PDBs) ---
kubectl drain $NODE \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --force \
  --grace-period=60 \
  --timeout=10m

# --- 2. Confirm no non-DaemonSet pods left ---
kubectl get pods -A --field-selector=spec.nodeName=$NODE \
  -o custom-columns='NAME:.metadata.name,NS:.metadata.namespace,KIND:.metadata.ownerReferences[0].kind' \
  --no-headers | grep -vE "DaemonSet|Node"
# Expect: empty (or just Static pods on control-plane)

# --- 3. Apply apt upgrades ---
ssh -i ~/.ssh/id_ed25519_k8s -o StrictHostKeyChecking=no imcbeth@$IP "
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get autoremove -y
"

# --- 4. Reboot ---
ssh -i ~/.ssh/id_ed25519_k8s -o StrictHostKeyChecking=no imcbeth@$IP "sudo reboot" || true
# ssh will drop; that's expected.

# --- 5. Wait for node to come back Ready ---
until kubectl get node $NODE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | grep -q True; do
  echo "  waiting for $NODE Ready..."
  sleep 15
done
echo "  $NODE is Ready"

# --- 6. Verify kernel bumped ---
ssh -i ~/.ssh/id_ed25519_k8s -o StrictHostKeyChecking=no imcbeth@$IP "uname -r; test -f /var/run/reboot-required && echo 'STILL needs reboot' || echo 'clean'"
# Expect: the kernel apt just installed (check `ls /boot/vmlinuz-*`) + clean
# NOTE: kubelet's Node.status.nodeInfo.kernelVersion lags a minute or two after
# reboot — `uname -r` over ssh is authoritative for what's actually running.

# --- 7. Uncordon ---
kubectl uncordon $NODE

# --- 8. Post-reboot observation window (~5-10 min) ---
# Watch for: fresh pods scheduling cleanly, no PVC RO cascade, no alerts
kubectl get pods -A --field-selector=spec.nodeName=$NODE -o wide --no-headers | head -20
PROM=prometheus-kube-prometheus-stack-prometheus-0
kubectl -n default exec $PROM -c prometheus -- \
  wget -qO- 'http://localhost:9090/api/v1/query?query=count(pvc_mount_readonly==1)' \
  | python3 -c "import json,sys;r=json.load(sys.stdin)['data']['result'];print('  RO mounts:',r[0]['value'][1] if r else 0)"

# Move to next node when: node Ready + PVC RO = 0 + no alerts firing
```

## Post-cycle validation

After all 5 nodes have rebooted:

```bash
# 1. All nodes on new kernel
for ip in 10.0.10.214 10.0.10.235 10.0.10.211 10.0.10.244 10.0.10.220; do
  ssh -i ~/.ssh/id_ed25519_k8s -o StrictHostKeyChecking=no imcbeth@$ip "uname -r"
done
# Expect: 6.8.0-1060-raspi (or newer) on all 5

# 2. Full cluster healthcheck
# Run the /cluster-healthcheck skill

# 3. Chaos-mesh next Wed audit — scripts/verify-chaos-week.sh
```

## Cluster-specific risks

Same shape as the k8s 1.36 upgrade:

1. **PVC RO cascade during drain** — pvc-ro-remediator auto-heals within ~4 min. Watch nodes with iSCSI PVCs. **NOTE (verified 2026-07-31): workload placement has drifted from the original baseline.** Current: **Prometheus AND Loki are both on node01**, Falco Redis on node02. Draining node01 re-attaches TWO iSCSI PVCs simultaneously — watch that drain most closely. Re-check placement the day of the run with: `for p in "default prometheus-kube-prometheus-stack-prometheus-0" "loki loki-0" "falco falco-falcosidekick-ui-redis-0"; do kubectl get pod -n ${p% *} ${p#* } -o jsonpath='{.metadata.name} -> {.spec.nodeName}{"\n"}'; done`
2. **Gatekeeper PDB drain wait** — **RESOLVED** by PR #845 (2 replicas + hard anti-affinity). If drains still hang here, that PR didn't apply cleanly — check `kubectl get deploy -n gatekeeper-system gatekeeper-controller-manager -o jsonpath='{.spec.replicas}'` = 2 and `.spec.template.spec.affinity.podAntiAffinity.requiredDuringScheduling...` exists.
3. **Chaos-mesh Wed fires** — not applicable if you run this on a Sat/Sun as planned.
4. **etcd on control-plane** — the control-plane reboot briefly stops the api-server. During the ~1-2 min window, `kubectl` commands will fail. Everything comes back automatically once the control-plane is back Ready.

## Rollback

Individual node reboot rollback: not applicable — reboot always brings the node back on the currently-installed kernel. If the new kernel doesn't boot, connect via console/UART or physical access to grub-boot the previous kernel.

apt upgrade rollback: `sudo apt-get install <package>=<old-version>` per package. Complex — better to test one node fully before doing the rest.

## After the runbook

- [ ] Update CURRENT.md with the reboot cycle results
- [ ] Update `k8s-docs-n37/docs/kubernetes/cluster-configuration.md` — bump kernel version row
- [ ] Note any packages that hit compatibility issues (worth capturing as REFERENCE.md gotcha)
