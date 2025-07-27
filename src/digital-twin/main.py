import logging
import json
import os
import psutil
import coloredlogs
from flask import Flask, request
from datetime import datetime
from waitress import serve

# UNIFIED AND COLORED LOGGING CONFIGURATION
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
coloredlogs.install(level='INFO', fmt=LOG_FORMAT, isatty=True)
logger = logging.getLogger("DigitalTwin")
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

app = Flask(__name__)
process = psutil.Process(os.getpid())

STATE_STORAGE_PATH = "/app/twin_state"
if not os.path.exists(STATE_STORAGE_PATH):
    os.makedirs(STATE_STORAGE_PATH)

def update_twin_state(alert_data):
    sensor_id = alert_data.get("sensor_id", "unknown_sensor")
    alert_type = alert_data.get("alert_type", "GENERIC_ALERT")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    state_file_path = os.path.join(STATE_STORAGE_PATH, f"{sensor_id}.state")
    logger.info(f"Received alert '{alert_type}' for '{sensor_id}'. Persisting state.")
    try:
        with open(state_file_path, "a") as f:
            f.write(f"[{timestamp}] - {alert_type}: {json.dumps(alert_data)}\n")
    except Exception as e:
        logger.error(f"Failed to persist state for {sensor_id}: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "ok"}, 200

@app.route('/update', methods=['POST'])
def receive_alert():
    mem_before_kb = process.memory_info().rss / 1024
    alert_payload = request.get_json(silent=True) or {}
    if not alert_payload:
        logger.warning("Received an empty update request.")
        return {"status": "empty_request"}, 400
    
    update_twin_state(alert_payload)
    
    mem_after_kb = process.memory_info().rss / 1024
    mem_diff_kb = mem_after_kb - mem_before_kb
    logger.info(f"State updated. RAM usage delta: {mem_diff_kb:.4f} KB")
    
    return {"status": "twin_state_updated"}, 200

if __name__ == "__main__":
    logger.info(f"Service starting on port 5000. State storage: {STATE_STORAGE_PATH}")
    serve(app, host='0.0.0.0', port=5000)