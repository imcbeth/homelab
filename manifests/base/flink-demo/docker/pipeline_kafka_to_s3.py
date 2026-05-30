#!/usr/bin/env python3
"""
Kafka-to-S3 Pipeline
Reads JSON events from a Kafka topic and writes each record as an individual
JSON object to S3 (LocalStack). Runs as a streaming job until cancelled.

Output layout:
  s3://flink-output/events/<YYYY>/<MM>/<DD>/<HH>/<uuid>.json
"""
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config

from pyflink.common import SimpleStringSchema, Types, WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaOffsetsInitializer, KafkaSource
from pyflink.datastream.functions import MapFunction

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("kafka-to-s3")

KAFKA_BROKERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "kafka-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092",
)
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "flink-events")
KAFKA_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "flink-kafka-to-s3")
S3_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://localstack.localstack.svc.cluster.local:4566")
S3_BUCKET = os.getenv("S3_BUCKET", "flink-output")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
AWS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "test")


class S3SinkFunction(MapFunction):
    """
    Flink MapFunction that writes each Kafka event to S3 as an individual JSON object.
    boto3 client is initialised once per task slot (open() lifecycle method).
    """

    def open(self, runtime_context) -> None:
        logger.info(
            "S3SinkFunction.open() — endpoint=%s  bucket=%s  region=%s",
            S3_ENDPOINT, S3_BUCKET, AWS_REGION,
        )
        self._s3 = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            region_name=AWS_REGION,
            aws_access_key_id=AWS_KEY_ID,
            aws_secret_access_key=AWS_SECRET,
            config=Config(retries={"max_attempts": 3, "mode": "standard"}),
        )
        logger.info("S3 client ready")

    def map(self, raw: str) -> str:
        # Deserialise
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Non-JSON payload received — wrapping in envelope: %r", raw[:80])
            record = {"raw": raw}

        # Enrich with pipeline metadata
        now = datetime.now(timezone.utc)
        record["pipeline_stage"] = "kafka-to-s3"
        record["written_at"] = now.isoformat()

        # Write to S3 partitioned by date/hour for easy querying
        key = f"events/{now.strftime('%Y/%m/%d/%H')}/{uuid.uuid4()}.json"
        body = json.dumps(record, indent=2).encode()

        self._s3.put_object(Bucket=S3_BUCKET, Key=key, Body=body)

        s3_uri = f"s3://{S3_BUCKET}/{key}"
        logger.info(
            "Written %-60s | id=%-4s  product=%-22s  price=$%s",
            s3_uri,
            record.get("id", "?"),
            record.get("product", "?"),
            record.get("price", "?"),
        )
        return s3_uri


def main() -> None:
    logger.info("=" * 70)
    logger.info("Flink Pipeline: Kafka → S3")
    logger.info("  Broker  : %s", KAFKA_BROKERS)
    logger.info("  Topic   : %s  (consumer group=%s)", KAFKA_TOPIC, KAFKA_GROUP)
    logger.info("  S3      : %s  bucket=%s", S3_ENDPOINT, S3_BUCKET)
    logger.info("  Mode    : streaming — runs until cancelled")
    logger.info("  Offsets : EARLIEST (replays all events on restart)")
    logger.info("=" * 70)

    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    logger.info("Building Kafka source — starting from EARLIEST offset")
    source = (
        KafkaSource.builder()
        .set_bootstrap_servers(KAFKA_BROKERS)
        .set_topics(KAFKA_TOPIC)
        .set_group_id(KAFKA_GROUP)
        .set_starting_offsets(KafkaOffsetsInitializer.earliest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    stream = env.from_source(
        source,
        WatermarkStrategy.no_watermarks(),
        f"Kafka[{KAFKA_TOPIC}]",
    )

    logger.info("Attaching S3SinkFunction — each Kafka record → individual S3 object")
    written_paths = stream.map(S3SinkFunction(), output_type=Types.STRING())

    # Print S3 paths to stdout — visible in task manager logs
    written_paths.print("→ S3")

    logger.info("Executing streaming job 'kafka-to-s3'...")
    logger.info("  To inspect output: kubectl exec -n localstack deploy/localstack -- awslocal s3 ls s3://flink-output/events/ --recursive")
    env.execute("kafka-to-s3")


if __name__ == "__main__":
    main()
