#!/bin/bash

set -e

# Use environment variables passed by 'docker compose run'.
TOTAL_LOOPS="${LOOPS:-5}"
TARGET_HOST="${TARGET_HOST:-dropper}"
TARGET_PORT="${TARGET_PORT:-5000}"
REQUESTS="${REQUESTS:-500}"
CONCURRENCY="${CONCURRENCY:-20}"
TARGET_URL="http://${TARGET_HOST}:${TARGET_PORT}/data"
RESULTS_DIR="/app/results"
mkdir -p $RESULTS_DIR

echo "Running benchmark against: ${TARGET_URL}"
echo "Configuration: ${TOTAL_LOOPS} loops, ${REQUESTS} requests, ${CONCURRENCY} concurrency."
echo "---------------------------------------------"

# 1. Wait for services to be ready
sleep 10

# 2. Prepare payload files
cat > /app/small_standard_payload.json << EOL
{
    "timestamp": "2025-01-01T12:00:00.000Z", "line_id": "BENCHMARK-LINE", "sensor_id": "vibration-test", "type": "vibration",
    "x": 5.0, "y": 3.0, "z": 8.5, "unit": "mm/s"
}
EOL
cat > /app/small_secure_payload.json << EOL
{
    "source": "secure",
    "encrypted_payload": "gAAAAABm_chB7YwX5a9z5v-c5u_QzJ8g6n_H9i_E6b9x0g_J3f_V2a8k8l9o_P4c3t_R2e_A1n_B1o_T1e_L0o_Z0c_V5d_Q0a_A=="
}
EOL

# 3. Run benchmark tests
for i in $(seq 1 ${TOTAL_LOOPS}); do
  echo -n "Running Loop ${i}/${TOTAL_LOOPS}... "
  
  ab -q -n ${REQUESTS} -c ${CONCURRENCY} -p /app/small_standard_payload.json -T 'application/json' \
    -g "${RESULTS_DIR}/standard_data_${i}.tsv" "${TARGET_URL}" > "${RESULTS_DIR}/standard_report_${i}.txt"
  
  ab -q -n ${REQUESTS} -c ${CONCURRENCY} -p /app/small_secure_payload.json -T 'application/json' \
    -g "${RESULTS_DIR}/secure_data_${i}.tsv" "${TARGET_URL}" > "${RESULTS_DIR}/secure_report_${i}.txt"
  
  echo "[DONE]"
done
echo "---------------------------------------------"