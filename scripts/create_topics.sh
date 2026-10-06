#!/usr/bin/env bash
set -euo pipefail

BOOTSTRAP="${KAFKA_BOOTSTRAP:-localhost:9092}"

TOPICS=(
  "sec.raw"
  "sec.normalized"
  "sec.detections"
  "sec.dlq"
)

echo "Creating Kafka topics..."

for topic in "${TOPICS[@]}"; do
  if kafka-topics --bootstrap-server "$BOOTSTRAP" \
      --list | grep -Fxq "$topic"; then
    echo "[skip] $topic already exists"
  else
    if [ "$topic" = "sec.dlq" ]; then
      kafka-topics --bootstrap-server "$BOOTSTRAP" \
        --create \
        --topic "$topic" \
        --partitions 1 \
        --replication-factor 1
    else
      kafka-topics --bootstrap-server "$BOOTSTRAP" \
        --create \
        --topic "$topic" \
        --partitions 3 \
        --replication-factor 1
    fi

    echo "[created] $topic"
  fi
done

echo "Kafka topics ready."