# Flink 1.20, not 2.x: the FlinkDeployments declare flinkVersion v1_20, and
# PyFlink and the Kafka connector below are 1.20 builds. Renovate moved this
# line to 2.3 in PR #784 (2026-06) and the image was never rebuilt, so the
# running flink-demo:1.0.0 was still Flink 1.20.4 while this file said 2.3.
# renovate.json now keeps apache/flink on 1.20.x; moving to Flink 2 means
# PyFlink 2, a Flink 2 connector and flinkVersion v2_x together.
FROM apache/flink:1.20.5-java17

# Current JDK. The official apache/flink images are rebuilt rarely (1.20.5:
# 2026-06-25), so their Temurin falls months behind; flink-demo:1.0.0 ran
# 17.0.19 (April). Replace it in place with a Temurin JDK: JAVA_HOME stays
# /opt/java/openjdk, and the JDK's include/ is what PyFlink's pemja compiles
# against, so Ubuntu's openjdk-17-jdk-headless (a second, older Java that
# Trivy also flagged) is no longer installed. 17.0.21.1 (the Java4Shell fix,
# CVE-2026-114938) had no arm64 image on 2026-11-21; that CVE is in an
# x86-64 AVX-512 path and does not apply on these ARM64 nodes.
COPY --from=eclipse-temurin:17.0.21_9-jdk-jammy /opt/java/openjdk /opt/java/openjdk

# Python 3 for PyFlink, plus a compiler for pemja (no arm64 wheel).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        curl \
        build-essential \
        python3-dev && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# PyFlink matches the base image's Flink version. The wheels are large
# (PyFlink bundles ~300 MB of jars); pip's 15 s default read timeout failed
# a test build, hence the longer timeout and retries.
RUN pip3 install --no-cache-dir --default-timeout=120 --retries 5 \
    apache-flink==1.20.5 \
    boto3==1.34.0

# Download the Kafka connector JAR compatible with Flink 1.20
# This enables both KafkaSink (file-to-kafka) and KafkaSource (kafka-to-s3)
RUN curl -fsSL \
    "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.20/flink-sql-connector-kafka-3.3.0-1.20.jar" \
    -o /opt/flink/lib/flink-sql-connector-kafka-3.3.0-1.20.jar && \
    echo "Downloaded flink-sql-connector-kafka-3.3.0-1.20.jar"

# Pipeline scripts are mounted from ConfigMaps at /opt/flink/scripts/ at runtime.
# The directory must exist for the mount to succeed.
RUN mkdir -p /opt/flink/scripts

# Verify Java, Python and PyFlink are working
RUN java -version && python3 -c "import pyflink; print('PyFlink OK')"
