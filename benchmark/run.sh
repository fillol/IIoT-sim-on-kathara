#!/bin/bash

set -e

COMPOSE_FILE="docker-compose.benchmark.yml"
PROJECT_NAME="src"
RESULTS_DIR="results"
STATS_FILE="${RESULTS_DIR}/stats.csv"
TOTAL_LOOPS=5
REQUESTS=500
CONCURRENCY=20

# 1. Clean previous run and create results directory
echo -n "Preparing results directory..."
rm -rf ./${RESULTS_DIR}
mkdir -p $RESULTS_DIR
echo " [OK]"

# 2. Start services using the dedicated benchmark compose file
echo -n "Bringing services down..."
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans > /dev/null 2>&1
echo " [OK]"

echo -n "Building and starting services for benchmark..."
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up --build -d > /dev/null 2>&1
echo " [OK]"

echo "Waiting 15 seconds for services to initialize..."
sleep 15
echo

# 3. Start resource monitoring
CONTAINER_IDS=$(docker compose -f $COMPOSE_FILE -p $PROJECT_NAME ps -q)
if [ -z "$CONTAINER_IDS" ]; then
    echo "Error: No running containers found for project '$PROJECT_NAME'. Exiting."
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans > /dev/null 2>&1
    exit 1
fi

(
  echo "Name,CPUPerc,MemUsage" > $STATS_FILE
  CRITICAL_CONTAINER_NAME="${PROJECT_NAME}-dropper-1"
  while docker ps --filter "name=${CRITICAL_CONTAINER_NAME}" --filter "status=running" | grep -q "${CRITICAL_CONTAINER_NAME}"; do
    docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" $CONTAINER_IDS >> $STATS_FILE
    sleep 2
  done
) &
MONITOR_PID=$!
echo "Monitoring started in background (PID: $MONITOR_PID)."
echo

# 4. Run the performance benchmark
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm \
  -e LOOPS=${TOTAL_LOOPS} \
  -e REQUESTS=${REQUESTS} \
  -e CONCURRENCY=${CONCURRENCY} \
  benchmark
echo "Benchmark finished."
echo

# 5. Teardown
echo -n "Stopping resource monitoring..."
kill $MONITOR_PID 2>/dev/null || true
wait $MONITOR_PID 2>/dev/null || true
echo " [OK]"

echo -n "Stopping all services..."
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans > /dev/null 2>&1
echo " [OK]"
echo

# 6. Final Report Generation
python3 report_generator.py --results-dir $RESULTS_DIR --stats-file $STATS_FILE --project-name $PROJECT_NAME