#!/bin/bash

TARGET_HOST="dropper"
TARGET_PORT="5000"
TARGET_URL="http://${TARGET_HOST}:${TARGET_PORT}/data"
REQUESTS=500
CONCURRENCY=20

# Create a directory for results
mkdir -p /app/results

echo "--- Starting IIoT Microservices Benchmark ---"
echo "Target URL: ${TARGET_URL}"
echo "Total Requests: ${REQUESTS}"
echo "Concurrency Level: ${CONCURRENCY}"
echo "---------------------------------------------"

# 1. Wait for services to initialize.
echo "Waiting 10 seconds for services to initialize..."
sleep 10
echo "Wait time finished. Starting tests."
echo "---------------------------------------------"

# 2. Prepare payload files for ab
echo "Preparing payload files..."
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

# 3. Run Benchmark Tests
echo "Running Test 1: Small Standard Payload..."
ab -n ${REQUESTS} -c ${CONCURRENCY} -p /app/small_standard_payload.json -T 'application/json' -g /app/results/standard_data.tsv ${TARGET_URL} > /app/results/standard_report.txt
echo "Test 1 finished. Report saved to results/standard_report.txt"
echo "---------------------------------------------"

echo "Running Test 2: Small Secure Payload..."
ab -n ${REQUESTS} -c ${CONCURRENCY} -p /app/small_secure_payload.json -T 'application/json' -g /app/results/secure_data.tsv ${TARGET_URL} > /app/results/secure_report.txt
echo "Test 2 finished. Report saved to results/secure_report.txt"
echo "---------------------------------------------"

# 4. Generate Final Report
echo "All tests finished. Generating statistical summary..."
python3 /app/generate_report.py
echo "--- Benchmark Complete ---"