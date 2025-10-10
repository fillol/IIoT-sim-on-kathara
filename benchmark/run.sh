#!/bin/bash
set -e

# Global Configuration
COMPOSE_FILE="compose-benchmark.yml"
PROJECT_NAME="iiot-kathara"
RESULTS_DIR="results"
TOTAL_LOOPS=3

DEFAULT_REQUESTS=100
DEFAULT_CONCURRENCY=2
DEFAULT_TIMEOUT=60

# Environment Preparation
echo "===> Cleaning and preparing environment"
rm -rf ./${RESULTS_DIR}
mkdir -p $RESULTS_DIR
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans --volumes > /dev/null 2>&1
echo "===> Building 'benchmark' image (if needed)"
docker compose -f $COMPOSE_FILE -p $PROJECT_NAME build benchmark > /dev/null
echo "===> Checking and building application images from project root..."
docker compose -f ../compose.yml -p $PROJECT_NAME build > /dev/null
echo "===> Generating required payloads"
PAYLOAD_SECURE=$(python3 -c "import json; from cryptography.fernet import Fernet; from datetime import datetime, timezone; key = b'u25A1N5g-jPAAZ_2CBl2i8o_HAG8AAnYq0_s2An1gE0='; cipher = Fernet(key); payload = {'timestamp': datetime.now(timezone.utc).isoformat(), 'line_id': 'BENCH-SECURE', 'sensor_id': 'security-test', 'type': 'security', 'status_code': 401}; encrypted = cipher.encrypt(json.dumps(payload).encode('utf-8')); print(json.dumps({'source': 'secure', 'encrypted_payload': encrypted.decode('utf-8')}))")
PAYLOAD_SECURE_IMAGE=$(python3 -c "import base64, json, sys; from cryptography.fernet import Fernet; from datetime import datetime, timezone; key = b'u25A1N5g-jPAAZ_2CBl2i8o_HAG8AAnYq0_s2An1gE0='; cipher = Fernet(key); image_path = '../src/publisher1/images/tents.jpg'; encoded_string = base64.b64encode(open(image_path, 'rb').read()).decode('utf-8'); payload = {'timestamp': datetime.now(timezone.utc).isoformat(), 'line_id': 'BENCH-IMG', 'sensor_id': 'image-test', 'type': 'image_security', 'image_filename': 'benchmark_image.jpg', 'image_data': encoded_string}; encrypted = cipher.encrypt(json.dumps(payload).encode('utf-8')); print(json.dumps({'source': 'secure', 'encrypted_payload': encrypted.decode('utf-8')}))")
PAYLOAD_IMAGE_DECRYPTED=$(python3 -c "import base64, json, sys; from datetime import datetime, timezone; image_path = '../src/publisher1/images/tents.jpg'; encoded_string = base64.b64encode(open(image_path, 'rb').read()).decode('utf-8'); payload = {'timestamp': datetime.now(timezone.utc).isoformat(), 'line_id': 'BENCH-IMG', 'sensor_id': 'image-test', 'type': 'image_security', 'image_filename': 'benchmark_image.jpg', 'image_data': encoded_string}; print(json.dumps(payload))")
echo "Payloads generated."
SUMMARY_FILE="${RESULTS_DIR}/summary_report.txt"
echo "Profile                  Idle_CPU(%) Idle_RAM(MiB) Avg_CPU(%)  Avg_RAM(MiB)  Avg_Latency(ms)  Std_Dev(ms)   Throughput(Mbps)" > $SUMMARY_FILE

declare -A IDLE_METRICS_CACHE
declare -A PROFILE_SERVICE_MAP=(
    ["DigitalTwin"]="digital-twin"
    ["Decrypter"]="decrypter"
    ["Dropper_StandardPath"]="dropper"
    ["Dropper_SecurePath"]="dropper"
    ["Dropper_SecureImagePath"]="dropper"
    ["FaultDetector_Standard"]="fault-detector"
    ["FaultDetector_Image"]="fault-detector"
)

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

calculate_throughput() {
    local ab_report_file=$1
    local total_sent=$(grep "Total body sent" "$ab_report_file" | awk '{print $4}')
    local time_taken=$(grep "Time taken for tests" "$ab_report_file" | awk '{print $5}')
    if [[ -z "$total_sent" || -z "$time_taken" || $(echo "$time_taken == 0" | bc -l) -eq 1 ]]; then
        echo "0.0000"; return
    fi
    python3 -c "print(f'{(($total_sent * 8) / ($time_taken * 1024 * 1024)):.4f}')"
}

measure_and_cache_idle_state() {
    local service_to_measure=$1
    if [ -n "${IDLE_METRICS_CACHE[$service_to_measure]}" ]; then
        return
    fi

    echo -n "--> Measuring idle state for '${service_to_measure}'..."
    docker compose -f ../compose.yml -p ${PROJECT_NAME} up -d ${service_to_measure} > /dev/null 2>&1
    sleep 15
    
    local container_name="${PROJECT_NAME}-${service_to_measure}-1"
    local idle_cpu_perc="0.00"
    local idle_mem_mib="0.00"

    if docker ps --filter "name=${container_name}" --filter "status=running" | grep -q "${container_name}"; then
        local stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" "${container_name}")
        idle_cpu_perc=$(echo "$stats" | awk -F, '{gsub(/%/, "", $1); print $1}')
        local mem_usage_str=$(echo "$stats" | awk -F, '{print $2}' | awk '{print $1}')
        idle_mem_mib=$(python3 -c "val='$mem_usage_str'; print(float(val.replace('GiB','')) * 1024 if 'GiB' in val else float(val.replace('MiB','')) if 'MiB' in val else float(val.replace('KiB','')) / 1024 if 'KiB' in val else 0.0)")
    fi
    
    IDLE_METRICS_CACHE[$service_to_measure]="${idle_cpu_perc},${idle_mem_mib}"
    docker compose -f ../compose.yml -p ${PROJECT_NAME} down --volumes > /dev/null 2>&1
    echo " Done."
    sleep 2
}

run_profile_test() {
    local service_to_start=$1
    local service_to_monitor=$2
    local host_port=$3
    local test_endpoint=$4
    local payload_content=$5
    local profile_name=$6
    local requests=${7:-$DEFAULT_REQUESTS}
    local concurrency=${8:-$DEFAULT_CONCURRENCY}
    local timeout_seconds=${9:-$DEFAULT_TIMEOUT}

    echo -e "\n===> PROFILING: ${profile_name} (Req: ${requests}, Conc: ${concurrency}, Timeout: ${timeout_seconds}s)"

    local service_for_idle_check=${PROFILE_SERVICE_MAP[$profile_name]}
    measure_and_cache_idle_state "$service_for_idle_check"
    local idle_metrics=${IDLE_METRICS_CACHE[$service_for_idle_check]}
    local idle_cpu=$(echo "$idle_metrics" | cut -d',' -f1)
    local idle_ram=$(echo "$idle_metrics" | cut -d',' -f2)

    declare -a results_cpu=() results_ram=() results_latency=() results_std_dev=() results_throughput=()

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
        
        kill $monitor_pid 2>/dev/null || true; sleep 1 
        docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down --volumes > /dev/null 2>&1
        
        local resources=$(awk -F, '{ gsub(/%/, "", $1); cpu += $1; split($2, ram_parts, " / "); used_ram = ram_parts[1]; if (used_ram ~ /GiB/) { gsub(/GiB/, "", used_ram); ram += used_ram * 1024; } else if (used_ram ~ /MiB/) { gsub(/MiB/, "", used_ram); ram += used_ram; } else if (used_ram ~ /KiB/) { gsub(/KiB/, "", used_ram); ram += used_ram / 1024; } count++ } END { if(count>0) print cpu/count, ram/count; else print "0,0"}' "${host_stats_file}")
        results_cpu+=($(echo $resources | cut -d' ' -f1))
        results_ram+=($(echo $resources | cut -d' ' -f2))

        local latency_stats=$(python3 -c "import sys, numpy as np; d = np.loadtxt('${host_ab_tsv_file}', skiprows=1, usecols=4, delimiter='\t', ndmin=1); print('{:.4f},{:.4f}'.format(np.mean(d), np.std(d))) if d.size > 0 else print('0.0,0.0')")
        results_latency+=($(echo $latency_stats | cut -d',' -f1))
        results_std_dev+=($(echo $latency_stats | cut -d',' -f2))
        
        results_throughput+=($(calculate_throughput "$host_ab_report_file"))
    done

    local final_cpu=$(printf "%s\n" "${results_cpu[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    local final_ram=$(printf "%s\n" "${results_ram[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    local final_latency=$(printf "%s\n" "${results_latency[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    local final_std_dev=$(printf "%s\n" "${results_std_dev[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    local final_throughput=$(printf "%s\n" "${results_throughput[@]}" | awk '{ total += $1; n++ } END { if (n > 0) print total / n; else print 0; }')
    
    LC_NUMERIC=C printf "%-25s %-11.4f %-13.4f %-11.4f %-13.4f %-16.4f %-13.4f %-12.4f\n" "$profile_name" "$idle_cpu" "$idle_ram" "$final_cpu" "$final_ram" "$final_latency" "$final_std_dev" "$final_throughput" >> $SUMMARY_FILE
}

echo -e "\n================================================="
echo "STARTING MICROSERVICES PROFILING SUITE"
echo "================================================="

export POISSON_LAMBDA=0

run_profile_test "digital-twin" "digital-twin" 5001 "/update" '{"sensor_id":"dt-test","alert_type":"BenchmarkAlert", "line_id": "BENCH-DT"}' "DigitalTwin"
run_profile_test "decrypter" "decrypter" 5002 "/decrypt" "${PAYLOAD_SECURE}" "Decrypter"
run_profile_test "dropper" "dropper" 5000 "/data" '{"type":"vibration","x":4.0, "sensor_id": "vibration-test", "line_id": "BENCH-VIB"}' "Dropper_StandardPath"
run_profile_test "dropper" "dropper" 5000 "/data" "${PAYLOAD_SECURE}" "Dropper_SecurePath"
run_profile_test "dropper" "dropper" 5000 "/data" "${PAYLOAD_SECURE_IMAGE}" "Dropper_SecureImagePath"
run_profile_test "fault-detector" "fault-detector" 5003 "/data" '{"type":"quality","defect_count":6, "sensor_id": "quality-test", "line_id": "BENCH-STD"}' "FaultDetector_Standard"
run_profile_test "fault-detector" "fault-detector" 5003 "/data" "${PAYLOAD_IMAGE_DECRYPTED}" "FaultDetector_Image"

echo -e "\n================================================="
echo "PROFILING COMPLETED. FINAL SUMMARY:"
echo "================================================="
column -t < $SUMMARY_FILE
echo "================================================="
echo "The raw data for each test is available in the 'results/' folder"