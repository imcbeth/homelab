# Control-Plane Hardening: Audit Logging + Encryption at Rest

**Drafted:** 2026-10-29, from the security review that produced PRs #1086–#1092
**Status:** NOT STARTED — both items are for a maintenance window, by decision
**Owner:** operator (this runbook)

## Why this is a runbook and not a PR

Everything else from the 2026-10-29 security review shipped as an ordinary
GitOps change. These two cannot, for one reason: **there is exactly one
control-plane node and exactly one etcd member.**

```
control-plane        v1.36.3   Ubuntu 24.04.5 LTS
etcd-control-plane   1/1 Running
```

Both changes are edits to `/etc/kubernetes/manifests/kube-apiserver.yaml`, a
static pod. The kubelet restarts the API server the moment that file is
written. A typo, a missing volume mount, or an unparseable policy file takes
the API server down — and with it kubectl, ArgoCD, and the ability to fix the
problem by any means other than SSH to 10.0.10.214.

That is recoverable. It is not recoverable *remotely and quickly*, which is
why it belongs in a window where the cluster is already expected to wobble —
most naturally alongside Phase 0 of [`k8s-1.37-upgrade.md`](k8s-1.37-upgrade.md),
which already plans an apiserver restart for the 1.36.3 → 1.36.5 patch.

## Current state, measured 2026-10-29

```bash
kubectl get pod -n kube-system -l component=kube-apiserver \
  -o jsonpath='{.items[0].spec.containers[0].command}'
```

| Flag | State | Consequence |
|---|---|---|
| `--audit-policy-file` | **absent** | No record of who changed what. |
| `--audit-log-path` | **absent** | — |
| `--encryption-provider-config` | **absent** | All 103 Secrets are stored **unencrypted** in etcd. |
| `--authorization-mode` | `Node,RBAC` | correct |
| `--enable-admission-plugins` | `NodeRestriction` | correct |

The audit gap has already cost us once. On 2026-10-28 a node was found
cordoned with no way to attribute it. `pvc-ro-remediator` stamps its own
cordons with an annotation, so *its* cordons are identifiable — but a cordon
from any other source, a human or a stray script, leaves no trace at all.
That investigation ended in a guess. With an audit log it would have ended in
a username.

The encryption gap matters because of what is in those Secrets: the
SealedSecrets private keys themselves live in `kube-system`. Anyone who reads
the etcd data file off the NAS, or out of a Velero backup, gets every secret
in the cluster **and** the keys that decrypt every `*-sealed.yaml` in this
repository. git-crypt protects the repo. It does nothing for etcd.

---

# Part 1 — Audit logging

Do this one **first and separately.** It is lower risk than Part 2, it is
trivially reversible, and it is the thing that makes Part 2 easier to
diagnose if Part 2 goes wrong.

## Risk

A malformed policy file makes the API server **fail to start**. The kubelet
keeps retrying it, so the outage lasts until the file is fixed.

Mitigation: validate the YAML, and keep a known-good copy of the original
manifest *before* touching anything.

## Steps

All commands run on the control-plane node unless stated otherwise.

```bash
ssh -i ~/.ssh/id_ed25519_k8s imcbeth@10.0.10.214
```

### 1. Back up the manifest first

Not optional. This is the entire rollback plan.

```bash
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml \
        /root/kube-apiserver.yaml.pre-audit
sudo ls -l /root/kube-apiserver.yaml.pre-audit
```

### 2. Write the audit policy

Into `/etc/kubernetes/audit-policy.yaml`. This policy is deliberately narrow:
`RequestResponse` on everything would fill a Pi's disk in days.

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - RequestReceived
rules:
  # The thing we actually wanted: who cordons and drains nodes.
  - level: RequestResponse
    verbs: ["update", "patch", "create", "delete"]
    resources:
      - group: ""
        resources: ["nodes", "nodes/status"]

  # Secret and config access, metadata only — never log the payloads.
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets", "configmaps", "serviceaccounts/token"]

  # RBAC changes always get a full record; they are rare.
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["*"]

  # Exec and port-forward into pods.
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/portforward", "pods/attach"]

  # Drop the firehose. These are the high-volume readers and would
  # otherwise be the overwhelming majority of the log.
  - level: None
    users:
      - "system:kube-scheduler"
      - "system:kube-controller-manager"
      - "system:apiserver"
      - "system:kube-proxy"
    verbs: ["get", "list", "watch"]
  - level: None
    userGroups: ["system:nodes"]
    verbs: ["get", "list", "watch"]
  - level: None
    nonResourceURLs:
      - "/healthz*"
      - "/readyz*"
      - "/livez*"
      - "/version"
      - "/metrics"

  # Everything else: one line per mutating call, nothing for reads.
  - level: Metadata
    verbs: ["create", "update", "patch", "delete", "deletecollection"]
  - level: None
```

Validate it parses before going anywhere near the manifest:

```bash
python3 -c "import yaml; d=yaml.safe_load(open('/etc/kubernetes/audit-policy.yaml')); \
  print('kind:', d['kind'], 'rules:', len(d['rules']))"
```

### 3. Create the log directory

```bash
sudo mkdir -p /var/log/kubernetes/audit
sudo chmod 700 /var/log/kubernetes/audit
```

### 4. Edit the static pod manifest

Add to `spec.containers[0].command`:

```yaml
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
    - --audit-log-path=/var/log/kubernetes/audit/audit.log
    - --audit-log-maxage=30
    - --audit-log-maxbackup=5
    - --audit-log-maxsize=100
```

`maxsize=100` MB × `maxbackup=5` caps the audit log at **500 MB**. Confirm the
control-plane root filesystem has room for that before committing to it —
these are Pi 5s, not servers.

Add to `spec.volumes`:

```yaml
  - name: audit-policy
    hostPath:
      path: /etc/kubernetes/audit-policy.yaml
      type: File
  - name: audit-log
    hostPath:
      path: /var/log/kubernetes/audit
      type: DirectoryOrCreate
```

Add to `spec.containers[0].volumeMounts`:

```yaml
    - name: audit-policy
      mountPath: /etc/kubernetes/audit-policy.yaml
      readOnly: true
    - name: audit-log
      mountPath: /var/log/kubernetes/audit
      readOnly: false
```

**The `type: File` on the policy volume matters.** With `DirectoryOrCreate` —
the type every other volume in that manifest uses, so the one you will reach
for by habit — the kubelet would helpfully create a *directory* named
`audit-policy.yaml` if the file were missing, and the API server would fail
with a confusing error about reading a directory.

Mind the `readOnly: false` on the log mount too. It is the only writable
mount in that pod, and inheriting `readOnly: true` by copy-paste from the
neighbouring entries is the easy mistake here.

### 5. Wait for the restart, then verify

The kubelet notices the change within ~20 seconds and restarts the pod.

```bash
# from the workstation
kubectl get pod -n kube-system -l component=kube-apiserver
kubectl get --raw /readyz
```

Then confirm it is actually *writing*, which is what proves the mounts are
right rather than merely accepted:

```bash
ssh -i ~/.ssh/id_ed25519_k8s imcbeth@10.0.10.214 \
  "sudo wc -l /var/log/kubernetes/audit/audit.log"
```

And confirm the policy does the job it was written for — cordon a node and
find yourself in the log:

```bash
kubectl cordon node04 && kubectl uncordon node04

ssh -i ~/.ssh/id_ed25519_k8s imcbeth@10.0.10.214 \
  "sudo grep -c 'nodes' /var/log/kubernetes/audit/audit.log"
```

If that count is zero, the policy is loaded but not matching, and the whole
exercise has achieved nothing. Do not skip this check — "the apiserver came
back up" is not the same as "auditing works".

### 6. Rollback, if needed

```bash
sudo cp /root/kube-apiserver.yaml.pre-audit \
        /etc/kubernetes/manifests/kube-apiserver.yaml
```

The kubelet restarts the API server from the restored file. Nothing else to
undo.

### 7. Ship the log somewhere

Optional, and a separate change. Alloy already runs as a DaemonSet on every
node and ships to Loki; pointing it at `/var/log/kubernetes/audit/audit.log`
on the control-plane node would put the audit trail in Grafana alongside
everything else. Worth doing — but not in the same window. A local file is
already infinitely better than nothing.

---

# Part 2 — Encryption at rest

Do this **only after Part 1 has been running for a while.** It is the riskier
of the two, and having an audit log makes diagnosing it much easier.

## Risk

Higher than Part 1, and of a different kind. Part 1 fails loudly and reverts
cleanly. **Part 2 can fail quietly and permanently:** once Secrets are
written encrypted, losing `/etc/kubernetes/enc/encryption-config.yaml` makes
**every one of the 103 Secrets in etcd unreadable, forever** — including the
SealedSecrets private keys, which would in turn make every `*-sealed.yaml` in
this repo undecryptable.

So backing up the key is not a step in this procedure. It is the
precondition.

## Steps

### 1. Snapshot etcd before anything else

```bash
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /root/etcd-pre-encryption.db

sudo ETCDCTL_API=3 etcdctl snapshot status /root/etcd-pre-encryption.db -w table
```

Copy that snapshot **off the node**.

### 2. Generate the key and write the config

```bash
sudo mkdir -p /etc/kubernetes/enc && sudo chmod 700 /etc/kubernetes/enc
head -c 32 /dev/urandom | base64      # <- the key
```

Into `/etc/kubernetes/enc/encryption-config.yaml`:

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      # Order matters. aescbc first means NEW writes are encrypted;
      # identity second means EXISTING plaintext reads still work, so
      # nothing breaks the moment this is loaded.
      - aescbc:
          keys:
            - name: key1
              secret: <the base64 key from above>
      - identity: {}
```

```bash
sudo chmod 600 /etc/kubernetes/enc/encryption-config.yaml
```

### 3. Back up the key somewhere that is not this cluster

**Before the API server ever reads the file.** Not the NAS the cluster
depends on. And not only in a Velero backup, whose bucket credentials are
themselves a Secret in the etcd you just encrypted. A password manager, or an
offline copy.

### 4. Edit the manifest

Same backup-first discipline as Part 1:

```bash
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml \
        /root/kube-apiserver.yaml.pre-encryption
```

Add the flag:

```yaml
    - --encryption-provider-config=/etc/kubernetes/enc/encryption-config.yaml
```

Plus the matching volume (`type: File`, read-only) and volumeMount, exactly
as in Part 1 step 4.

### 5. Verify NEW writes are encrypted

The provider order means nothing has changed for existing Secrets yet. Prove
the new path works on a throwaway Secret before touching the real ones:

```bash
kubectl create secret generic enc-canary -n default --from-literal=k=v

sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/default/enc-canary | hexdump -C | head -5
```

Expect `k8s:enc:aescbc:v1:key1:` near the start. If `v` is readable in
plaintext, **stop** — the config is not being applied, and step 6 would
accomplish nothing but churn.

```bash
kubectl delete secret enc-canary -n default
```

### 6. Re-encrypt the existing 103 Secrets

This rewrites every Secret through the new provider:

```bash
kubectl get secrets -A -o json | kubectl replace -f -
```

Spot-check a real one in etcd afterwards — ideally a SealedSecrets key, since
that is the prize:

```bash
sudo ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/kube-system/ --prefix --keys-only | grep sealed-secrets-key | head -1
```

### 7. Only then consider removing `identity`

Dropping the `identity` provider is what makes the encryption
non-reversible-by-accident. Leave it in place for a good while. It costs
nothing: new writes are already encrypted, and `identity` only ever serves as
a fallback for reads of anything step 6 missed.

### 8. Rollback

Before step 6: restore the pre-encryption manifest. Done.

After step 6: the `identity` provider is why this is still survivable —
restoring the manifest makes previously-encrypted Secrets unreadable, so the
real rollback is the etcd snapshot from step 1. Which is why step 1 is
step 1.

---

## Checklist

Part 1 — audit logging:

- [ ] `/root/kube-apiserver.yaml.pre-audit` exists
- [ ] policy file parses as YAML
- [ ] root filesystem has room for 500 MB of logs
- [ ] apiserver `Running`, `/readyz` ok
- [ ] `audit.log` is growing
- [ ] a deliberate cordon appears in it
- [ ] (later, separately) Alloy ships it to Loki

Part 2 — encryption at rest:

- [ ] etcd snapshot taken AND copied off the node
- [ ] key backed up outside this cluster
- [ ] `/root/kube-apiserver.yaml.pre-encryption` exists
- [ ] canary Secret shows `k8s:enc:aescbc:v1:key1:` in etcd
- [ ] all Secrets re-encrypted
- [ ] a SealedSecrets key verified encrypted in etcd
- [ ] `identity` provider deliberately left in place
