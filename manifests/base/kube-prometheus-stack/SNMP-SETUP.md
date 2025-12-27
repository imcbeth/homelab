# SNMP Exporter Setup Guide

This guide explains how to configure SNMP monitoring for your Synology NAS using SNMPv3 authentication.

**Note:** This configuration uses the new auth-split format introduced in SNMP exporter v0.23.0+.

## Overview

The SNMP exporter monitors your Synology NAS (10.0.1.204) and exposes metrics to Prometheus including:
- Disk status and temperature
- RAID status
- CPU temperature
- Fan status
- Storage usage
- Network statistics

## Prerequisites

### 1. Enable SNMPv3 on Synology NAS

1. Log into Synology DSM
2. Go to **Control Panel → Terminal & SNMP**
3. Click the **SNMP** tab
4. Enable **Enable SNMP service**
5. Select **SNMPv3 service**
6. Click **SNMPv3 Settings**

### 2. Create SNMPv3 User on Synology

In the SNMPv3 Settings dialog:

1. Click **Create**
2. Enter user information:
   - **User**: `snmp_monitor` (or your chosen username)
   - **Authentication**: Check "Enable authentication"
   - **Protocol**: SHA (recommended)
   - **Password**: Choose a strong password (min 8 characters)
   - **Privacy**: Check "Enable privacy"
   - **Protocol**: AES (recommended)
   - **Password**: Choose a strong privacy password (min 8 characters)
3. Click **OK**
4. Apply changes

## Configuration Steps

### 1. Update SNMP Credentials Secret

Edit `manifests/base/kube-prometheus-stack/snmp-exporter-secret.yaml`:

```yaml
stringData:
  snmp-username: "snmp_monitor"              # Match Synology user
  snmp-auth-password: "your_auth_password"   # Your authentication password
  snmp-priv-password: "your_priv_password"   # Your privacy password
  snmp-auth-protocol: "SHA"                  # SHA or MD5
  snmp-priv-protocol: "AES"                  # AES or DES
```

**IMPORTANT:** This file should be encrypted with git-crypt before committing!

### 2. Configuration Structure (New Auth-Split Format)

The new format separates authentication from module configuration:

**snmp-exporter-configmap.yaml structure:**
```yaml
data:
  snmp.yml: |
    auths:
      synology_v3:
        version: 3
        username: snmp_monitor        # Must match secret
        security_level: authPriv
        password: YOUR_AUTH_PASSWORD  # Placeholder - actual value in secret
        auth_protocol: SHA
        priv_protocol: AES
        priv_password: YOUR_PRIV_PASSWORD

    modules:
      synology:
        walk: [...]
        metrics: [...]
```

**Prometheus scrape configuration:**
```yaml
- job_name: 'snmp-synology'
  params:
    auth: [synology_v3]  # References the auth section
    module: [synology]   # References the module section
```

**Note:** The ConfigMap uses placeholders. You must manually update the ConfigMap after deploying with the actual passwords, OR regenerate the ConfigMap from a template.

### 3. Test SNMP Access (Optional)

Before deploying, test SNMP access from your local machine:

```bash
# Install snmpwalk (if not already installed)
# macOS: brew install net-snmp
# Linux: apt-get install snmp

# Test SNMPv3 connection
snmpwalk -v3 \
  -l authPriv \
  -u snmp_monitor \
  -a SHA -A "your_auth_password" \
  -x AES -X "your_priv_password" \
  10.0.1.204 \
  1.3.6.1.4.1.6574.1.1
```

Expected output: Should return system status value

## Deployment

Once configured, ArgoCD will automatically deploy:
1. SNMP exporter pod
2. SNMP configuration (ConfigMap)
3. SNMP credentials (Secret)
4. Prometheus scrape configuration

## Verify Deployment

### Check SNMP Exporter Pod

```bash
kubectl get pods -n default | grep snmp-exporter
```

Expected: `snmp-exporter-xxx   1/1   Running`

### Check SNMP Exporter Logs

```bash
kubectl logs -n default deployment/snmp-exporter
```

Look for successful startup, no authentication errors.

### Test Metrics Endpoint

```bash
# Port-forward to SNMP exporter
kubectl port-forward -n default svc/snmp-exporter 9116:9116

# Query Synology metrics with auth-split format
curl "http://localhost:9116/snmp?auth=synology_v3&module=synology&target=10.0.1.204"
```

Expected: Should return Prometheus-formatted metrics

### Verify Prometheus Scraping

```bash
# Port-forward to Prometheus
kubectl port-forward -n default svc/kube-prometheus-stack-prometheus 9090:9090
```

Open http://localhost:9090/targets and look for:
- Job: `snmp-synology`
- State: UP
- Target: `10.0.1.204`

## Troubleshooting

### Authentication Failed

**Symptom:** SNMP exporter logs show authentication errors

**Solutions:**
1. Verify SNMPv3 user exists on Synology
2. Check username matches in secret and ConfigMap
3. Verify auth and priv passwords are correct
4. Ensure auth/priv protocols match (SHA/AES)

### Timeout Errors

**Symptom:** SNMP queries timeout

**Solutions:**
1. Verify Synology NAS is reachable: `ping 10.0.1.204`
2. Check SNMP service is enabled on Synology
3. Verify firewall allows SNMP (UDP port 161)
4. Increase scrape_timeout in Prometheus config

### No Metrics

**Symptom:** Metrics endpoint returns empty or errors

**Solutions:**
1. Verify SNMP walks are correct for Synology
2. Check SNMP exporter logs for OID errors
3. Test with snmpwalk to verify OIDs are accessible
4. Ensure Synology user has read permissions

### Wrong Security Level

**Symptom:** "security level not supported" error

**Solutions:**
- Ensure Synology user has both authentication and privacy enabled
- security_level must be `authPriv` for both auth and encryption

## Example Grafana Queries

Once metrics are flowing, use these PromQL queries:

```promql
# Disk temperature
diskTemperature

# RAID status (1=Normal, anything else is a problem)
raidStatus != 1

# System temperature
temperature

# Storage usage percentage
(hrStorageUsed / hrStorageSize) * 100
```

## Security Notes

1. **Always use SNMPv3** - SNMPv1/v2c send community strings in cleartext
2. **Strong passwords** - Use minimum 12 characters for auth and priv passwords
3. **SHA + AES** - Use SHA (not MD5) and AES (not DES) for best security
4. **Encrypt secrets** - Use git-crypt to encrypt the secret file before committing
5. **Read-only** - SNMP user should have read-only access (no write permissions)

## Reference

- SNMP Exporter: https://github.com/prometheus/snmp_exporter
- Synology SNMP OIDs: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Firmware/DSM/All/enu/Synology_DiskStation_MIB_Guide.pdf
- Reference config: `~/homelab/snmp.yml`
