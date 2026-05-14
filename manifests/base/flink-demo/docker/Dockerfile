FROM apache/flink:1.20-java17

# Install Python 3 and pip (ARM64 compatible — base image is multi-arch)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        curl && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install PyFlink (must match the Flink base image version) and pipeline deps
RUN pip3 install --no-cache-dir \
    apache-flink==1.20.0 \
    boto3==1.34.0

# Download the Kafka connector JAR compatible with Flink 1.20
# This enables both KafkaSink (file-to-kafka) and KafkaSource (kafka-to-s3)
RUN curl -fsSL \
    "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.20/flink-sql-connector-kafka-3.3.0-1.20.jar" \
    -o /opt/flink/lib/flink-sql-connector-kafka-3.3.0-1.20.jar && \
    echo "Downloaded flink-sql-connector-kafka-3.3.0-1.20.jar"

# Copy pipeline scripts into the image as fallback
# (ConfigMaps mounted at /opt/flink/scripts/ take precedence at runtime)
RUN mkdir -p /opt/flink/scripts
COPY pipeline_file_to_kafka.py /opt/flink/scripts/
COPY pipeline_kafka_to_s3.py   /opt/flink/scripts/

# Verify Python and PyFlink are working
RUN python3 -c "import pyflink; print('PyFlink', pyflink.__version__, 'OK')"
