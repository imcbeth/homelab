---
session: 2026-05-31
title: "Flink Demo Pipeline — End-to-End Working (file→Kafka→S3)"
---

## Completed Work

Three bugs fixed across three PRs to get the pipeline end-to-end:

**PR #637: flink-webhook OOMKill (128Mi → 256Mi)**
- The flink-webhook JVM was OOMKilling at 128Mi during TLS crypto ops, causing EOF on every API server webhook call → FlinkDeployments couldn't be created.
- Fix: `webhook.resources.limits.memory: 256Mi` in `manifests/base/flink-operator/values.yaml`

**PR #638: FlinkDeployment memory 512m → 1Gi**
- With `resource.memory: "512m"`, JVM overhead (192mb) + JVM Metaspace (256mb) = 448mb, leaving only 64mb for Total Flink Memory vs 128mb off-heap default.
- Error: `Total Flink Memory (64mb) < Off-heap Memory (128mb)`
- Fix: Changed jobManager and taskManager memory to `"1Gi"` in both FlinkDeployment YAMLs.

**PR #639: `env.from_collection()` type_info=Types.STRING()**
- Without explicit type info, PyFlink uses Kryo to serialize elements. Kryo serializes Python strings as Java byte arrays (`[B`). KafkaSink's `SimpleStringSchema.serialize()` then fails casting `[B` → `String`.
- Error: `ClassCastException: class [B cannot be cast to class java.lang.String`
- Fix: `env.from_collection(records, type_info=Types.STRING())` in `pipeline-file-to-kafka-configmap.yaml`

**Also fixed: Dockerfile pemja build issue (previous session, image build)**
- `pemja==0.4.1` requires JDK headers, GCC, Python headers to compile C extension.
- Added `openjdk-17-jdk-headless`, `build-essential`, `python3-dev` + header symlink.

## Final Verified State

- `flink-events:0:15` — 15 JSON records in Kafka ✅
- `s3://flink-output/events/2026/05/31/14/*.json` — 15 individual JSON files in LocalStack S3 ✅
- `file-to-kafka` FlinkDeployment: FINISHED/STABLE ✅ (batch job, replays on restart)
- `kafka-to-s3` FlinkDeployment: RUNNING/STABLE ✅ (streaming, consuming new messages)

## Key Gotchas

- **flink-webhook JVM needs ≥256Mi**: TLS crypto is memory-intensive. 128Mi causes OOMKill → EOF on all webhook calls.
- **Flink memory model minimum**: With 1Gi, breakdown is: JVM Overhead 192mb + JVM Metaspace 256mb + JVM Heap 448mb + Off-heap 128mb = 1024mb. 512mb leaves only 64mb for Flink which is below the 128mb off-heap default.
- **PyFlink from_collection() type safety**: Always pass `type_info=Types.STRING()` (or appropriate type) to `env.from_collection()`. Without it, Kryo serialization converts Python strings to `[B` byte arrays, breaking any Java-side String sink.
- **FAILED FlinkDeployment restart**: The operator doesn't restart a FAILED job on ConfigMap change — it requires a spec change. Delete the old JobManager pod to force the Deployment controller to recreate it; the new pod picks up the updated ConfigMap.

## Pull Requests

- **PR #637:** [Merged] fix: increase flink-webhook memory limit to 256Mi (OOMKill)
- **PR #638:** [Merged] fix: bump FlinkDeployment memory from 512m to 1Gi
- **PR #639:** [Merged] fix: add type_info=Types.STRING() to from_collection in file-to-kafka
