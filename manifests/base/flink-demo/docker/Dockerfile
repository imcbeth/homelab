# Flink 2.2 (2026-11-21). 2.2 is the newest line the Flink Kubernetes
# Operator here (1.16.1) accepts as flinkVersion (v2_2); keep the base image,
# PyFlink, the Kafka connector and flinkVersion in the FlinkDeployments on
# the same minor (renovate.json caps apache/flink below 2.3 for that reason).
#
# Why 2.x: the gate in flink-demo-build blocked a Flink 1.20 rebuild on
# pyarrow 11.0.0 (CVE-2023-47248, critical, fixed in 14.0.1). PyFlink 1.20
# pins apache-beam<2.49, which pins pyarrow<12, so 1.20 cannot be fixed.
# PyFlink 2.2 allows apache-beam up to 2.61, which allows pyarrow<17.
FROM apache/flink:2.2.1-java17

# Flink 2.x images set USER flink (1.20 images built as root). Install as
# root, then hand the image back to flink (uid 9999, which the FlinkDeployment
# podTemplates also run as) at the end.
USER root

# Current JDK. The official apache/flink images are rebuilt rarely (2.2.1:
# 2026-06-25) and ship Temurin 17.0.19 (April). Replace it in place:
# JAVA_HOME stays /opt/java/openjdk, and the JDK's include/ is what PyFlink's
# pemja compiles against. 17.0.21.1 (the Java4Shell fix, CVE-2026-114938) had
# no arm64 image on 2026-11-21; that CVE is in an x86-64 AVX-512 path and
# does not apply on these ARM64 nodes.
COPY --from=eclipse-temurin:17.0.21.1_2-jdk-noble /opt/java/openjdk /opt/java/openjdk

# Python 3 for PyFlink, plus a compiler (PyFlink and pemja have no
# linux/aarch64 wheels and build from source).
# apt over HTTPS: the in-cluster build may only reach the internet on 443,
# and Ubuntu's sources use http (port 80). Ubuntu 24.04 keeps them in
# sources.list.d/ubuntu.sources (deb822); sources.list is kept for older
# layouts. ca-certificates is already in the base image.
RUN sed -i 's|http://ports.ubuntu.com|https://ports.ubuntu.com|g' \
        /etc/apt/sources.list /etc/apt/sources.list.d/ubuntu.sources && \
    apt-get update && \
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

# PyFlink matches the base image's Flink version. pyarrow is pinned to the
# fixed range explicitly, so a resolver change cannot quietly bring 11.x back.
# The wheels are large (PyFlink bundles ~300 MB of jars); pip's 15 s default
# read timeout failed a test build, hence the longer timeout and retries.
# --break-system-packages: Ubuntu 24.04 marks the system Python as externally
# managed (PEP 668); this image has one job, and PyFlink runs `python`.
RUN pip3 install --no-cache-dir --break-system-packages \
        --default-timeout=120 --retries 5 \
    apache-flink==2.2.1 \
    "pyarrow>=14.0.1,<17" \
    boto3==1.34.0

# Kafka connector for Flink 2.2 (KafkaSink in file-to-kafka, KafkaSource in
# kafka-to-s3).
RUN curl -fsSL \
    "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/5.0.0-2.2/flink-sql-connector-kafka-5.0.0-2.2.jar" \
    -o /opt/flink/lib/flink-sql-connector-kafka-5.0.0-2.2.jar && \
    echo "Downloaded flink-sql-connector-kafka-5.0.0-2.2.jar"

# Pipeline scripts are mounted from ConfigMaps at /opt/flink/scripts/ at runtime.
# The directory must exist for the mount to succeed.
RUN mkdir -p /opt/flink/scripts && chown flink:flink /opt/flink/scripts /opt/flink/lib/flink-sql-connector-kafka-5.0.0-2.2.jar

USER flink

# Verify Java, Python and PyFlink are working
RUN java -version && python3 -c "import pyflink, pyarrow; print('PyFlink OK, pyarrow', pyarrow.__version__)"
