# Velero Backup Solution

Velero provides backup and disaster recovery for the Raspberry Pi 5 Kubernetes homelab cluster.

## Architecture

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

**Limitations:**
- ⚠️ Ephemeral storage - backups lost on LocalStack pod restart
- ✅ Good for testing and validation
- ❌ NOT suitable for production disaster recovery

### Backblaze B2 (Production - Recommended)

**Setup Steps:**
1. Sign up at https://www.backblaze.com/b2/
2. Create bucket: `velero-backups-homelab-n37`
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

**Costs:**
- Storage: $6/TB/month (~$0.60/month for 100Gi)
- Egress: Free for first 3x storage size
- Total: ~$1-2/month for homelab

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

# 3. Restore from backup
velero restore create grafana-pvc-restore \
  --from-backup daily-critical-pvcs-latest \
  --include-namespaces default \
  --include-resources pvc,pv

# 4. Wait for restore
velero restore describe grafana-pvc-restore --details

# 5. Scale up deployment
kubectl -n default scale deployment kube-prometheus-stack-grafana --replicas=1

# Time to recovery: < 15 minutes
```

**Scenario 2: Namespace Loss (loki)**
```bash
# 1. Restore entire namespace
velero restore create loki-restore \
  --from-backup daily-critical-pvcs-latest \
  --include-namespaces loki

# 2. Verify pods come up
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
  --from-backup weekly-cluster-resources-latest

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

```bash
# Verify S3 credentials
kubectl -n velero get secret velero-s3-credentials -o yaml

# Test S3 connectivity from Velero pod
kubectl -n velero exec deployment/velero -- velero backup-location get

# For LocalStack, verify LocalStack is running
kubectl -n localstack get pods

# Test LocalStack S3 endpoint
kubectl -n localstack exec deployment/localstack -- \
  awslocal s3 ls s3://velero-backups
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
4. ✅ S3 bucket created: `velero-backups-homelab-n37`

### Migration Steps

**Step 1: Update Configuration**

Edit `manifests/base/velero/values.yaml`:

```yaml
configuration:
  backupStorageLocation:
    - name: default
      provider: aws
      bucket: velero-backups-homelab-n37
      config:
        # For Backblaze B2:
        region: us-west-004
        s3Url: https://s3.us-west-004.backblazeb2.com
        # Remove: s3ForcePathStyle, insecureSkipTLSVerify

credentials:
  useSecret: true
  secretContents:
    cloud: |
      [default]
      aws_access_key_id=<YOUR_B2_KEY_ID>
      aws_secret_access_key=<YOUR_B2_APPLICATION_KEY>
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
7. **Secure Credentials**: Use git-crypt or external secret management
8. **Test Production Migration**: Validate S3 migration before relying on it

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

- **DAC_READ_SEARCH**: Allows the node-agent (Kopia) to read files from `/var/lib/kubelet/pods` regardless of their ownership or permissions. This is essential for backing up PVC data that may belong to different users.

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
