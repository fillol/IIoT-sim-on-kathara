#!/bin/bash

COMPOSE_FILE="local-test.yml"
STATS_OUTPUT_FILE="stats.csv"
PROJECT_NAME=$(basename "$PWD")
DROPPER_CONTAINER="${PROJECT_NAME}-dropper-1"
DECRYPTER_CONTAINER="${PROJECT_NAME}-decrypter-1"
FAULT_DETECTOR_CONTAINER="${PROJECT_NAME}-fault-detector-1"
DIGITAL_TWIN_CONTAINER="${PROJECT_NAME}-digital-twin-1"

echo "--- Preparing for benchmark run ---"
docker compose -f $COMPOSE_FILE down --remove-orphans
echo "Starting services in the background..."
docker compose -f $COMPOSE_FILE up --build -d production-line-1
echo "Waiting 10 seconds for all services to start..."
sleep 10

echo "--- Starting resource monitoring ---"
echo "Monitoring started. Data will be collected periodically."
(
  echo "Name,MemUsage" > $STATS_OUTPUT_FILE # Create header for CSV
  while docker inspect $DROPPER_CONTAINER > /dev/null 2>&1; do
    docker stats --no-stream --format "{{.Name}},{{.MemUsage}}" \
      $DROPPER_CONTAINER $DECRYPTER_CONTAINER $FAULT_DETECTOR_CONTAINER $DIGITAL_TWIN_CONTAINER \
      >> $STATS_OUTPUT_FILE
    sleep 2 # Collect data every 2 seconds
  done
) &
MONITOR_PID=$!

echo "Monitoring process started (PID: $MONITOR_PID)."

echo "--- Running the performance benchmark ---"
docker compose -f $COMPOSE_FILE run benchmark

echo "--- Benchmark finished. Stopping monitoring and services ---"
kill $MONITOR_PID

docker compose -f $COMPOSE_FILE down --remove-orphans

echo "--- Experiment complete. Raw data is in $STATS_OUTPUT_FILE ---"
echo "--- Run 'python3 analyze_stats.py' to see the summary. ---"