#!/bin/bash
set -e

# Global Configuration
COMPOSE_FILE="compose-benchmark.yml"
PROJECT_NAME="iiot-kathara"
RESULTS_DIR="results"
TOTAL_LOOPS=3

DEFAULT_REQUESTS=100
DEFAULT_CONCURRENCY=2

# Environment Preparation
echo "===> Cleaning and preparing environment"
rm -rf ./${RESULTS_DIR}
mkdir -p $RESULTS_DIR
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans --volumes > /dev/null 2>&1
echo "===> Building 'benchmark' image (if needed)"
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME build benchmark > /dev/null
echo "===> Checking and building application images from project root..."
docker compose -f ../compose.yml -p $PROJECT_NAME build > /dev/null

# Generate complex payloads (one-time)
echo "===> Generating required payloads"
PAYLOAD_SECURE=$(python3 -c "import json; from cryptography.fernet import Fernet; from datetime import datetime, timezone; key = b'u25A1N5g-jPAAZ_2CBl2i8o_HAG8AAnYq0_s2An1gE0='; cipher = Fernet(key); payload = {'timestamp': datetime.now(timezone.utc).isoformat(), 'line_id': 'BENCH-SECURE', 'sensor_id': 'security-test', 'type': 'security', 'status_code': 401}; encrypted = cipher.encrypt(json.dumps(payload).encode('utf-8')); print(json.dumps({'source': 'secure', 'encrypted_payload': encrypted.decode('utf-8')}))")
PAYLOAD_SECURE_IMAGE=$(python3 -c "import base64, json, sys; from cryptography.fernet import Fernet; from datetime import datetime, timezone; key = b'u25A1N5g-jPAAZ_2CBl2i8o_HAG8AAnYq0_s2An1gE0='; cipher = Fernet(key); image_path = '../src/publisher1/images/tents.jpg'; encoded_string = base64.b64encode(open(image_path, 'rb').read()).decode('utf-8'); payload = {'timestamp': datetime.now(timezone.utc).isoformat(), 'line_id': 'BENCH-IMG', 'sensor_id': 'image-test', 'type': 'image_security', 'image_filename': 'benchmark_image.jpg', 'image_data': encoded_string}; encrypted = cipher.encrypt(json.dumps(payload).encode('utf-8')); print(json.dumps({'source': 'secure', 'encrypted_payload': encrypted.decode('utf-8')}))")
PAYLOAD_IMAGE_DECRYPTED=$(python3 -c "import base64, json, sys; from datetime import datetime, timezone; image_path = '../src/publisher1/images/tents.jpg'; encoded_string = base64.b64encode(open(image_path, 'rb').read()).decode('utf-8'); payload = {'timestamp': datetime.now(timezone.utc).isoformat(), 'line_id': 'BENCH-IMG', 'sensor_id': 'image-test', 'type': 'image_security', 'image_filename': 'benchmark_image.jpg', 'image_data': encoded_string}; print(json.dumps(payload))")
echo "Payloads generated."

# File for the summary table
SUMMARY_FILE="${RESULTS_DIR}/summary_report.txt"
echo "Profile Avg_CPU(%) Avg_RAM(MiB) Avg_Latency(ms) Std_Dev(ms) Variance(ms^2)" > $SUMMARY_FILE

# Utility function
wait_for_service() {
    local service_name=$1
    local port=$2
    echo -n "Waiting for '${service_name}'..."
    for j in $(seq 1 30); do
        if curl --connect-timeout 1 -s "http://localhost:${port}/" > /dev/null; then
            echo " OK."
            return 0
        fi
        sleep 1
    done
    echo " ERROR: Timeout."
    exit 1
}

# Main atomic test function
run_profile_test() {
    local service_to_start=$1
    local service_to_monitor=$2
    local host_port=$3
    local test_endpoint=$4
    local payload_content=$5
    local profile_name=$6
    local requests=${7:-$DEFAULT_REQUESTS}
    local concurrency=${8:-$DEFAULT_CONCURRENCY}
    local timeout_seconds=${9:-30}

    echo -e "\n===> PROFILING: ${profile_name} (Req: ${requests}, Conc: ${concurrency}, Timeout: ${timeout_seconds}s)"

    declare -a results_cpu=()
    declare -a results_ram=()
    declare -a results_latency=()
    declare -a results_std_dev=()
    declare -a results_variance=()

    local profile_dir_host="${RESULTS_DIR}/${profile_name}"
    mkdir -p "${profile_dir_host}"

    for i in $(seq 1 ${TOTAL_LOOPS}); do
        echo -n "--> Loop ${i}/${TOTAL_LOOPS}... "
        
        docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d ${service_to_start} > /dev/null 2>&1
        wait_for_service "${service_to_monitor}" "${host_port}"

        local host_stats_file="${profile_dir_host}/loop_${i}_stats.csv"
        local host_ab_report_file="${profile_dir_host}/loop_${i}_ab_report.txt"
        local host_ab_tsv_file="${profile_dir_host}/loop_${i}_data.tsv"
        
        local container_profile_dir="/app/results/${profile_name}"
        local container_ab_tsv_file="${container_profile_dir}/loop_${i}_data.tsv"

        local monitor_container_name="${PROJECT_NAME}-${service_to_monitor}-1"
        
        (
          while docker ps --filter "name=${monitor_container_name}" --filter "status=running" | grep -q "${monitor_container_name}"; do
            docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" "${monitor_container_name}" >> "${host_stats_file}"
            sleep 1
          done
        ) &
        local monitor_pid=$!

        docker compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm benchmark /bin/bash -c "
          mkdir -p ${container_profile_dir} && \
          echo '${payload_content}' > /app/payload.json && \
          ab -q -n ${requests} -c ${concurrency} -s ${timeout_seconds} -p /app/payload.json -T 'application/json' -g ${container_ab_tsv_file} 'http://${service_to_monitor}:5000${test_endpoint}';
        " > "${host_ab_report_file}"
        
        kill $monitor_pid 2>/dev/null || true
        sleep 1 
        
        docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down --volumes > /dev/null 2>&1
        
        local resources=$(awk -F, '{
            gsub(/%/, "", $1);
            cpu += $1;
            
            split($2, ram_parts, " / ");
            used_ram = ram_parts[1];
            
            if (used_ram ~ /GiB/) {
                gsub(/GiB/, "", used_ram);
                ram += used_ram * 1024;
            } else if (used_ram ~ /MiB/) {
                gsub(/MiB/, "", used_ram);
                ram += used_ram;
            } else if (used_ram ~ /KiB/) {
                gsub(/KiB/, "", used_ram);
                ram += used_ram / 1024;
            }
            count++
        } END { if(count>0) print cpu/count, ram/count; else print "0,0"}' "${host_stats_file}")

        results_cpu+=($(echo $resources | cut -d' ' -f1))
        results_ram+=($(echo $resources | cut -d' ' -f2))

        local latency_stats=$(python3 -c "import sys, numpy as np; d = np.loadtxt('${host_ab_tsv_file}', skiprows=1, usecols=4, delimiter='\t', ndmin=1); print('{:.4f},{:.4f},{:.4f}'.format(np.mean(d), np.std(d), np.var(d))) if d.size > 0 else print('0.0,0.0,0.0')")
        results_latency+=($(echo $latency_stats | cut -d',' -f1))
        results_std_dev+=($(echo $latency_stats | cut -d',' -f2))
        results_variance+=($(echo $latency_stats | cut -d',' -f3))
    done

    local final_cpu=$(printf "%s\n" "${results_cpu[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    local final_ram=$(printf "%s\n" "${results_ram[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    local final_latency=$(printf "%s\n" "${results_latency[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    local final_std_dev=$(printf "%s\n" "${results_std_dev[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    local final_variance=$(printf "%s\n" "${results_variance[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    
    LC_NUMERIC=C printf "%-25s %.4f %.4f %.4f %.4f %.4f\n" $profile_name $final_cpu $final_ram $final_latency $final_std_dev $final_variance >> $SUMMARY_FILE
}

echo -e "\n================================================="
echo "STARTING MICROSERVICES PROFILING SUITE"
echo "================================================="

export POISSON_LAMBDA=0

run_profile_test "digital-twin" "digital-twin" 5001 "/update" '{"sensor_id":"dt-test","alert_type":"BenchmarkAlert"}' "DigitalTwin"
run_profile_test "decrypter" "decrypter" 5002 "/decrypt" "${PAYLOAD_SECURE}" "Decrypter"
run_profile_test "dropper" "dropper" 5000 "/data" '{"type":"vibration","x":4.0}' "Dropper_StandardPath"
run_profile_test "dropper" "dropper" 5000 "/data" "${PAYLOAD_SECURE}" "Dropper_SecurePath"
run_profile_test "dropper" "dropper" 5000 "/data" "${PAYLOAD_SECURE_IMAGE}" "Dropper_SecureImagePath" $DEFAULT_REQUESTS $DEFAULT_CONCURRENCY 120
run_profile_test "fault-detector" "fault-detector" 5003 "/data" '{"type":"quality","defect_count":6, "sensor_id": "quality-test", "line_id": "BENCH-STD"}' "FaultDetector_Standard"
run_profile_test "fault-detector" "fault-detector" 5003 "/data" "${PAYLOAD_IMAGE_DECRYPTED}" "FaultDetector_Image" $DEFAULT_REQUESTS $DEFAULT_CONCURRENCY 120

echo -e "\n================================================="
echo "PROFILING COMPLETED. FINAL SUMMARY:"
echo "================================================="
column -t < $SUMMARY_FILE
echo "================================================="
echo "The raw data for each test is available in the 'results/' folder"