# Velero Backup Solution

> ⚠️ **Important:** The default `values.yaml` configuration assumes LocalStack is deployed for S3 storage testing. Before deploying Velero, either:
> 1. Deploy LocalStack first (see [Prerequisites](#prerequisites)), OR
> 2. Configure Velero for production S3 storage (see [Option B](#option-b-configure-velero-for-production-s3-skip-localstack))
>
> If LocalStack is not available, Velero will fail to start with connection errors.

Velero provides backup and disaster recovery for the Raspberry Pi 5 Kubernetes homelab cluster.

## Architecture

> **Note:** The diagram below shows LocalStack as the S3 storage backend. This is the **default configuration for testing purposes**. LocalStack is **optional** - you can configure Velero to use production S3 providers (Backblaze B2, AWS S3, Wasabi, MinIO) instead. See the [Prerequisites](#prerequisites) section for options.

```
┌─────────────────────────────────────────────────────────┐
│ Velero Server (1 pod)                                   │
│ - 100m CPU / 256Mi RAM                                  │
│ - Manages backup/restore operations                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Node-Agent DaemonSet (5 pods, one per node)            │
│ - 100m CPU / 256Mi RAM per pod                          │
│ - Kopia file-level backup                              │
│ - Tolerates control-plane taint                        │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┴──────────────────┐
        ↓                                    ↓
┌──────────────────┐              ┌──────────────────────┐
│ CSI Snapshots    │              │ S3 Storage           │
│ - Synology CSI   │              │ - LocalStack (test)  │
│ - Fast recovery  │              │ - Future: B2 (prod)  │
└──────────────────┘              └──────────────────────┘
```

**Components:**
- **Velero Server**: Manages backup/restore operations, schedules
- **Node-Agent (Kopia)**: DaemonSet on all 5 nodes for file-level PVC backup
- **CSI Snapshots**: Storage-native snapshots via Synology CSI
- **S3 Storage**: Object storage for backup data (LocalStack for testing)

## Backup Strategy

### Daily Critical PVC Backup (2 AM)
- **Schedule**: Every day at 2:00 AM
- **Retention**: 30 days
- **Namespaces**: default (Prometheus, Grafana), loki, pihole
- **Method**: Kopia file-level + CSI snapshots
- **Total Data**: ~80Gi (Prometheus 50Gi, Loki 20Gi, Grafana 5Gi, Pi-hole 5Gi)

### Weekly Cluster Resource Backup (3 AM Sunday)
- **Schedule**: Every Sunday at 3:00 AM
- **Retention**: 90 days
- **Scope**: All cluster resources (ArgoCD apps, ConfigMaps, Secrets, etc.)
- **Method**: Kubernetes resource backup only (no PVCs)

## Critical PVCs Backed Up

| Component | Namespace | Size | Storage Class | Data Type |
|-----------|-----------|------|---------------|-----------|
| **Prometheus** | default | 50Gi | synology-iscsi-retain | Metrics TSDB (10-day retention) |
| **Loki** | loki | 20Gi | synology-iscsi-retain | Log chunks/TSDB (7-day retention) |
| **Grafana** | default | 5Gi | synology-iscsi-retain | Dashboards, datasources, plugins |
| **Pi-hole** | pihole | 5Gi | synology-iscsi-retain | DNS blocklists, query history |

## Prerequisites

### LocalStack Deployment (Required for Current Configuration)

The current `values.yaml` configuration assumes LocalStack is deployed and accessible. **Before installing or upgrading Velero**, verify LocalStack is running:

```bash
# 1. Check if LocalStack namespace exists
kubectl get namespace localstack

# 2. Verify LocalStack pod is running
kubectl get pods -n localstack

# 3. Verify LocalStack service exists and exposes port 4566
kubectl get service -n localstack localstack

# 4. Test LocalStack S3 endpoint connectivity
kubectl run -n velero --rm -i --tty test-localstack --image=amazon/aws-cli --restart=Never -- \
  s3 ls --endpoint-url=http://localstack.localstack:4566

# If the above command succeeds, LocalStack is accessible from within the cluster
```

**If LocalStack is NOT deployed:**

You have two options:

**Option A: Deploy LocalStack first** (Recommended for testing)

Deploy LocalStack before installing Velero. Example LocalStack deployment:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: localstack
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: localstack
  namespace: localstack
spec:
  replicas: 1
  selector:
    matchLabels:
      app: localstack
  template:
    metadata:
      labels:
        app: localstack
    spec:
      containers:
      - name: localstack
        image: localstack/localstack:3.8.1
        ports:
        - containerPort: 4566
        env:
        - name: SERVICES
          value: s3
---
apiVersion: v1
kind: Service
metadata:
  name: localstack
  namespace: localstack
spec:
  selector:
    app: localstack
  ports:
  - port: 4566
    targetPort: 4566
```

**Option B: Configure Velero for production S3** (Skip LocalStack)

If you want to skip LocalStack testing and go directly to production S3 (Backblaze B2, AWS S3, etc.), update `values.yaml` before deployment:

1. Comment out the LocalStack configuration in the `backupStorageLocation` section
2. Uncomment your production S3 provider configuration (e.g., Backblaze B2, AWS S3, Wasabi, or MinIO)
3. Update credentials to match your production S3 provider
4. See the "Migration from LocalStack to Production S3" section below for detailed steps

**Common Error Messages if LocalStack is Missing:**

If Velero is deployed without LocalStack being available, you'll see errors like:

```
BackupStorageLocation "default" is unavailable: rpc error: code = Unknown desc = Get "http://localstack.localstack:4566/": dial tcp: lookup localstack.localstack on 10.96.0.10:53: no such host
```

**Resolution:**
- Deploy LocalStack (Option A above), OR
- Reconfigure Velero for production S3 (Option B above)

## Storage Backends

### LocalStack (Testing - Current Configuration)
```yaml
config:
  region: us-east-1
  s3ForcePathStyle: "true"
  s3Url: http://localstack.localstack:4566
  insecureSkipTLSVerify: "true"

credentials:
  aws_access_key_id: test
  aws_secret_access_key: test
```

> **Note:** The credentials shown above (`test` / `test`) are for LocalStack testing only. These values must be consistent across:
> - Your Velero `values.yaml` configuration (under `credentials.secretContents`)
> - Your LocalStack deployment settings
>
> If these credentials don't match, Velero will fail to connect to the S3 endpoint.

**Limitations:**
- ⚠️ Ephemeral storage - backups lost on LocalStack pod restart
- ✅ Good for testing and validation
- ❌ NOT suitable for production disaster recovery

### Backblaze B2 (Production - Recommended)

**Setup Steps:**
1. Sign up at https://www.backblaze.com/b2/
2. Create bucket: `velero-backups-<YOUR-IDENTIFIER>` (e.g., `velero-backups-homelab-n37`)
3. Generate application key with read/write permissions
4. Update `values.yaml`:
   ```yaml
   config:
     region: us-west-004  # Your B2 region
     s3Url: https://s3.us-west-004.backblazeb2.com

   credentials:
     aws_access_key_id: <B2_KEY_ID>
     aws_secret_access_key: <B2_APPLICATION_KEY>
   ```

**Costs (assumptions & scaling):**
- Storage rate: $6/TB/month
  - Example: ~100Gi stored ≈ $0.60/month (100Gi is used as a round number slightly above the ~80Gi of critical data to allow for growth and metadata)
  - Estimate assumes 30 days of daily backups with incremental/deduplicated storage (i.e., not 30× full copies); actual usage depends on how much data changes between backups
  - As a rough guide, effective stored size will scale approximately with: `base data size × (1 + average daily change rate × retention days)`, capped by how well Kopia/Velero deduplicate unchanged blocks
- Egress: Free for the first 3× of total stored data size (per Backblaze B2 policy)
- Total cost: typically in the ~$1–2/month range for this homelab with ~80–100Gi of logical data and a 30‑day retention policy, assuming moderate daily change rates

## Manual Backup Commands

### Create Backups

```bash
# Backup specific namespace
velero backup create grafana-manual \
  --include-namespaces default \
  --selector app.kubernetes.io/name=grafana \
  --default-volumes-to-fs-backup

# Backup with CSI snapshot
velero backup create prometheus-snapshot \
  --include-namespaces default \
  --include-resources pvc,pv \
  --snapshot-volumes

# Backup entire cluster
velero backup create cluster-backup-$(date +%Y%m%d) \
  --include-cluster-resources=true \
  --default-volumes-to-fs-backup

# Backup single PVC
velero backup create loki-pvc-backup \
  --include-namespaces loki \
  --default-volumes-to-fs-backup \
  --wait
```

### View Backups

```bash
# List all backups
velero backup get

# Describe specific backup
velero backup describe daily-critical-pvcs-20251227020000

# View backup logs
velero backup logs daily-critical-pvcs-20251227020000

# Check backup in S3 (LocalStack)
kubectl -n localstack exec deployment/localstack -- \
  awslocal s3 ls s3://velero-backups/backups/
```

## Restore Commands

### Restore from Backup

```bash
# List available backups
velero backup get

# Restore from latest scheduled backup
velero restore create --from-backup daily-critical-pvcs-latest

# Restore specific namespace
velero restore create grafana-restore \
  --from-backup grafana-manual \
  --include-namespaces default

# Restore specific resources
velero restore create prometheus-pvc-restore \
  --from-backup prometheus-snapshot \
  --include-resources pvc,pv

# Check restore status
velero restore describe grafana-restore
velero restore logs grafana-restore

# List all restores
velero restore get
```

### Disaster Recovery Scenarios

**Scenario 1: Single PVC Loss (Grafana)**
```bash
# 1. Scale down deployment
kubectl -n default scale deployment kube-prometheus-stack-grafana --replicas=0

# 2. Delete PVC
kubectl -n default delete pvc kube-prometheus-stack-grafana

# 3. Find latest backup from the daily-critical-pvcs schedule
LATEST_BACKUP=$(velero backup get | awk '/^daily-critical-pvcs-/ {print $1}' | sort | tail -n 1)

# 4. Restore from backup
velero restore create grafana-pvc-restore \
  --from-backup "$LATEST_BACKUP" \
  --include-namespaces default \
  --include-resources pvc,pv

# 5. Wait for restore
velero restore describe grafana-pvc-restore --details

# 6. Scale up deployment
kubectl -n default scale deployment kube-prometheus-stack-grafana --replicas=1

# Time to recovery: < 15 minutes
```

**Scenario 2: Namespace Loss (loki)**
```bash
# 1. Identify most recent daily-critical-pvcs backup
LATEST_BACKUP=$(velero backup get | awk '/^daily-critical-pvcs-/ {print $1}' | sort | tail -n 1)

# 2. Restore entire namespace
velero restore create loki-restore \
  --from-backup "$LATEST_BACKUP" \
  --include-namespaces loki

# 3. Verify pods come up
kubectl get pods -n loki -w

# Time to recovery: < 30 minutes
```

**Scenario 3: Full Cluster Rebuild**
```bash
# 1. Deploy new Kubernetes cluster (same version)
# 2. Install Velero with same configuration
# 3. Point to same S3 bucket
# 4. Restore all namespaces

velero restore create cluster-restore \
  --from-backup weekly-cluster-resources-2024-12-01-000000

# Time to recovery: < 4 hours
```

## Testing Procedures

### Test 1: ConfigMap Backup/Restore

```bash
# Create test namespace and data
kubectl create namespace velero-test
kubectl -n velero-test create configmap test-data --from-literal=foo=bar

# Backup
velero backup create test-configmap \
  --include-namespaces velero-test \
  --wait

# Verify backup
velero backup describe test-configmap

# Delete namespace
kubectl delete namespace velero-test

# Restore
velero restore create test-restore \
  --from-backup test-configmap \
  --wait

# Verify restore
kubectl -n velero-test get configmap test-data -o yaml

# Cleanup
kubectl delete namespace velero-test
```

### Test 2: PVC Backup/Restore

```bash
# Create test PVC
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
  namespace: velero-test
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: synology-iscsi-retain
  resources:
    requests:
      storage: 1Gi
EOF

# Create test pod with data (PVC mounted at /data)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: velero-test
spec:
  restartPolicy: Never
  containers:
  - name: busybox
    image: busybox
    command: ["/bin/sh", "-c"]
    args: ["echo 'test data' > /data/test.txt && sleep 3600"]
    volumeMounts:
    - name: test-volume
      mountPath: /data
  volumes:
  - name: test-volume
    persistentVolumeClaim:
      claimName: test-pvc
EOF
# Backup with kopia file-level backup
velero backup create test-pvc-backup \
  --include-namespaces velero-test \
  --default-volumes-to-fs-backup \
  --wait

# Delete namespace
kubectl delete namespace velero-test

# Restore
velero restore create test-pvc-restore \
  --from-backup test-pvc-backup \
  --wait

# Verify data
kubectl -n velero-test get pvc
kubectl -n velero-test get pods

# Cleanup
kubectl delete namespace velero-test
```

### Test 3: Production PVC Backup (Non-destructive)

```bash
# Backup Pi-hole (smallest production PVC - 5Gi)
velero backup create test-pihole-backup \
  --include-namespaces pihole \
  --default-volumes-to-fs-backup \
  --snapshot-volumes \
  --wait

# Monitor backup progress
velero backup describe test-pihole-backup --details

# Check backup size and duration
velero backup get | grep test-pihole-backup

# Do NOT restore unless testing in non-production environment
```

## Monitoring

### Prometheus Metrics

Velero exports metrics that are automatically scraped by Prometheus:

```promql
# Backup success rate
velero_backup_success_total{schedule="daily-critical-pvcs"}

# Backup failure count
velero_backup_failure_total

# Backup duration
velero_backup_duration_seconds{schedule="daily-critical-pvcs"}

# Last successful backup timestamp
velero_backup_last_successful_timestamp

# Restore operations
velero_restore_success_total
velero_restore_failure_total
```

### View Metrics in Prometheus

```bash
# Port-forward Prometheus
kubectl port-forward -n default svc/kube-prometheus-stack-prometheus 9090:9090

# Navigate to http://localhost:9090/graph
# Query: velero_backup_success_total{schedule="daily-critical-pvcs"}
```

### Check Backup Health

```bash
# Pod status
kubectl get pods -n velero

# Backup storage location status
kubectl get backupstoragelocation -n velero

# Volume snapshot location status
kubectl get volumesnapshotlocation -n velero

# Recent backups
velero backup get

# Backup schedules
velero schedule get

# Velero server logs
kubectl -n velero logs deployment/velero

# Node-agent logs (per node)
kubectl -n velero logs daemonset/node-agent
```

## Troubleshooting

### Backup Failing

```bash
# Check backup status
velero backup describe <backup-name> --details

# View backup logs
velero backup logs <backup-name>

# Common issues:
# 1. S3 connectivity - check s3Url and credentials
# 2. CSI snapshot issues - check VolumeSnapshot CRDs
# 3. Kopia timeout - check node-agent logs and resource limits
```

### S3 Connection Issues

#### LocalStack Not Deployed or Unreachable

**Symptoms:**
```
BackupStorageLocation "default" is unavailable: rpc error: code = Unknown desc = Get "http://localstack.localstack:4566/": dial tcp: lookup localstack.localstack on 10.96.0.10:53: no such host
```

**Diagnosis:**
```bash
# 1. Verify LocalStack namespace exists
kubectl get namespace localstack
# If error "Error from server (NotFound): namespaces 'localstack' not found"
# → LocalStack is not deployed

# 2. Check if LocalStack pods are running
kubectl get pods -n localstack
# If no pods or pods are in CrashLoopBackOff
# → LocalStack deployment has issues

# 3. Verify LocalStack service exists
kubectl get service -n localstack localstack -o yaml
# Check that:
# - Service exists
# - spec.ports includes port 4566
# - Service selector matches LocalStack pod labels

# 4. Test connectivity from Velero namespace
kubectl run -n velero --rm -i --tty test-s3 --image=amazon/aws-cli --restart=Never -- \
  s3 ls --endpoint-url=http://localstack.localstack:4566
# If successful, LocalStack is reachable
# If connection refused or DNS error → LocalStack not accessible
```

**Resolution:**

Choose one of the following:

**A. Deploy LocalStack** (see Prerequisites section above)

**B. Reconfigure Velero for Production S3:**

1. Update `manifests/base/velero/values.yaml`:
   ```yaml
   configuration:
     backupStorageLocation:
       - name: default
         provider: aws
         bucket: velero-backups-YOUR-IDENTIFIER
         config:
           # For Backblaze B2:
           region: us-west-004
           s3Url: https://s3.us-west-004.backblazeb2.com
           # Remove LocalStack-specific settings:
           # - s3ForcePathStyle
           # - insecureSkipTLSVerify
   ```

2. Update credentials:

   Create a file named `cloud-credentials.txt`:
   ```
   [default]
   aws_access_key_id=YOUR_KEY_ID
   aws_secret_access_key=YOUR_SECRET_KEY
   ```

   Then create the secret:
   ```bash
   kubectl create secret generic cloud-credentials \
     -n velero \
     --from-file=cloud=cloud-credentials.txt

   # Clean up the credentials file
   rm cloud-credentials.txt
   ```

3. Restart Velero:
   ```bash
   kubectl rollout restart deployment/velero -n velero
   ```

4. Verify backup storage location:
   ```bash
   kubectl get backupstoragelocation -n velero
   # Status should change to "Available"
   ```

#### General S3 Connection Issues

```bash
# Verify S3 credentials
kubectl -n velero get secret cloud-credentials -o yaml

# Test S3 connectivity from Velero pod
kubectl -n velero exec deployment/velero -- velero backup-location get

# Check backup storage location status
kubectl get backupstoragelocation -n velero -o yaml

# View Velero server logs for connection errors
kubectl -n velero logs deployment/velero | grep -i "error\|failed"
```

#### For LocalStack Specifically

```bash
# Verify LocalStack is running
kubectl -n localstack get pods

# Check LocalStack logs
kubectl -n localstack logs deployment/localstack

# Test LocalStack S3 endpoint from LocalStack pod
kubectl -n localstack exec deployment/localstack -- \
  awslocal s3 ls s3://velero-backups

# Create bucket if it doesn't exist
kubectl -n localstack exec deployment/localstack -- \
  awslocal s3 mb s3://velero-backups
```

### CSI Snapshot Issues

```bash
# Check VolumeSnapshot CRDs
kubectl get volumesnapshot -A

# Check VolumeSnapshotContent
kubectl get volumesnapshotcontent

# Check Synology CSI snapshotter
kubectl get pods -n synology-csi

# Verify snapshot class
kubectl get volumesnapshotclass
```

### Node-Agent (Kopia) Issues

```bash
# Check node-agent pods
kubectl -n velero get pods -l name=node-agent -o wide

# View node-agent logs for specific node
kubectl -n velero logs daemonset/node-agent -c node-agent --tail=100

# Common issues:
# 1. Memory limits too low - increase from 1Gi to 1.5Gi
# 2. Backup timeout - increase timeout in backup spec
# 3. Permission issues - verify node-agent securityContext in values.yaml
#    Current config: privileged: false, capabilities: [DAC_READ_SEARCH]
#    If backups fail with permission errors:
#    a) Check node-agent logs for specific error messages
#    b) Verify /var/lib/kubelet/pods is accessible via hostPath
#    c) Consider adding SYS_ADMIN capability if DAC_READ_SEARCH is insufficient
#    d) Only use privileged: true as absolute last resort
```

### Restore Failing

```bash
# Check restore status
velero restore describe <restore-name> --details

# View restore logs
velero restore logs <restore-name>

# Common issues:
# 1. Namespace already exists - delete namespace first
# 2. PVC already exists - delete PVC first
# 3. Incompatible storage class - check storageClassName
```

## Migration from LocalStack to Production S3

### Prerequisites

1. ✅ LocalStack testing completed successfully
2. ✅ At least 3 successful backup/restore cycles
3. ✅ External S3 account created (Backblaze B2, AWS S3, Wasabi, etc.)
4. ✅ S3 bucket created: `velero-backups-<YOUR-IDENTIFIER>` (e.g., `velero-backups-homelab-n37`)

### Migration Steps

**Step 1: Update Configuration**

Edit `manifests/base/velero/values.yaml`:

```yaml
configuration:
  backupStorageLocation:
    - name: default
      provider: aws
      bucket: velero-backups-<YOUR-IDENTIFIER>  # Replace with your bucket name
      config:
        # For Backblaze B2:
        region: us-west-004
        s3Url: https://s3.us-west-004.backblazeb2.com
        # Remove: s3ForcePathStyle, insecureSkipTLSVerify

credentials:
  useSecret: true
  existingSecret: velero-b2-credentials        # Pre-created Kubernetes Secret
  # Note: Create the Secret manually before deploying:
  #   kubectl create secret generic velero-b2-credentials -n velero \
  #     --from-literal=cloud=$'[default]\naws_access_key_id=<YOUR_B2_KEY_ID>\naws_secret_access_key=<YOUR_B2_APPLICATION_KEY>'
```

**Step 2: Deploy Changes**

```bash
# Commit changes
git add manifests/base/velero/values.yaml
git commit -m "feat: Migrate Velero to production Backblaze B2 storage"
git push

# ArgoCD will auto-sync, or force sync:
argocd app sync velero --grpc-web
```

**Step 3: Verify Migration**

```bash
# Check backup storage location
kubectl get backupstoragelocation -n velero
# Status should be "Available"

# Create test backup to new location
velero backup create test-production-s3 \
  --include-namespaces velero-test \
  --wait

# Verify backup succeeded
velero backup describe test-production-s3

# Check backup exists in S3 bucket (using AWS CLI or B2 web UI)
```

**Step 4: Monitor Production Backups**

- Wait for first scheduled backup (2 AM daily)
- Verify backup completes successfully
- Check S3 storage usage and costs
- Monitor for 7 days to ensure stability

## Resource Impact

**Velero Server (1 pod):**
- CPU: 100m request / 200m limit
- Memory: 256Mi request / 512Mi limit

**Node-Agent DaemonSet (5 pods):**
- CPU: 500m request / 2.5 cores limit (total)
- Memory: 1.28Gi request / 5Gi limit (total)

**Total Cluster Overhead:**
- CPU: 600m (100m server + 500m node-agents) (~3% of 20 cores)
- Memory: 1.53Gi (256Mi server + 1.28Gi node-agents) (~1.9% of 80GB)

**Storage:**
- LocalStack: Ephemeral (no persistent storage)
- Production S3: ~100Gi (~$6-12/month for Backblaze B2)

## Backup Schedule Reference

| Schedule | Time | Frequency | Retention | Scope | Size |
|----------|------|-----------|-----------|-------|------|
| daily-critical-pvcs | 2 AM | Daily | 30 days | Prometheus, Loki, Grafana, Pi-hole | ~80Gi |
| weekly-cluster-resources | 3 AM Sunday | Weekly | 90 days | All cluster resources | ~100Mi |

## Best Practices

1. **Test Restores Regularly**: Monthly disaster recovery drills
2. **Monitor Backup Success**: Check Prometheus metrics daily
3. **Verify S3 Storage**: Monthly audit of S3 bucket and costs
4. **Update Retention Policies**: Adjust based on compliance needs
5. **Document Procedures**: Keep runbooks up-to-date
6. **Plan for Growth**: Monitor backup sizes and adjust resources
7. **Secure Credentials (IMPORTANT)**:
   - The example `values.yaml` uses plaintext `secretContents` **for local testing only**.
   - **Do not commit real credentials in plaintext** or deploy them as-is to production.
   - For production, store secrets outside of Git (e.g. external secret manager like Vault/ExternalSecrets, or encrypted files via `git-crypt`, `sops`, etc.) and override the example values.

   Example (override in your own `values.secure.yaml`):

   ```yaml
   # Do NOT store real secrets in this repo.
   # This file should be kept out of Git or encrypted with git-crypt/sops.
   credentials:
     existingSecret: cloud-credentials
     # secretContents in the base values are for example only and should be disabled/overridden
   ```

8. **Test Production Migration**: Validate S3 migration before relying on it for disaster recovery

## Security Considerations

### Node-Agent Capabilities

The Velero node-agent runs with **minimal Linux capabilities** instead of full privileged mode:

**Current Configuration:**
```yaml
containerSecurityContext:
  privileged: false
  allowPrivilegeEscalation: false
  capabilities:
    add:
      - DAC_READ_SEARCH  # Bypass file read permission checks
```

**Why This Configuration?**

- **DAC_READ_SEARCH (Discretionary Access Control - Read Search)**: Allows the node-agent (Kopia) to read files from `/var/lib/kubelet/pods` regardless of their ownership or permissions. This is essential for backing up PVC data that may belong to different users.

- **SYS_ADMIN Removed**: Previous versions included `SYS_ADMIN`, but this provides unnecessarily broad system administration privileges. Kopia file-system backups only need to read already-mounted volumes, which `DAC_READ_SEARCH` enables without the security risks of `SYS_ADMIN`.

- **CSI Snapshots**: The CSI snapshot operations (if enabled) are handled by the Velero server and CSI driver via the Kubernetes API, not by the node-agent, so they don't require additional node-agent capabilities.

**If You Experience Permission Issues:**

1. Check node-agent logs: `kubectl -n velero logs daemonset/node-agent -c node-agent`
2. Verify hostPath access to `/var/lib/kubelet/pods` is working
3. Check SELinux/AppArmor policies for compatibility
4. Verify PodSecurityPolicy/PodSecurityStandards allow `DAC_READ_SEARCH`
5. As a last resort, you may add `SYS_ADMIN` capability, but be aware of the security implications

**Comparison with Privileged Mode:**

| Configuration | Privileges | Security Risk | Recommendation |
|--------------|------------|---------------|----------------|
| `privileged: true` | All capabilities + host access | Very High | ❌ Avoid |
| `capabilities: [SYS_ADMIN]` | Broad system admin | High | ⚠️ Only if necessary |
| `capabilities: [DAC_READ_SEARCH]` | File read bypass only | Low | ✅ Recommended |

## References

- [Velero Documentation](https://velero.io/docs/)
- [Velero CSI Snapshot Support](https://velero.io/docs/main/csi/)
- [Velero File System Backup (Kopia)](https://velero.io/docs/v1.15/file-system-backup/)
- [Backblaze B2 with Velero](https://www.backblaze.com/blog/kubernetes-backups-with-backblaze-b2-and-velero/)
- [Kubernetes Backup on Raspberry Pi](https://picluster.ricsanfre.com/docs/backup/)
