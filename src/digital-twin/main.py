import logging
import json
import os
from flask import Flask, request
from datetime import datetime

# LOGGING
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)
logger = logging.getLogger("DigitalTwin")

app = Flask(__name__)

# This path simulates the persistent storage for the Digital Twin's state.
STATE_STORAGE_PATH = "/app/twin_state"
if not os.path.exists(STATE_STORAGE_PATH):
    os.makedirs(STATE_STORAGE_PATH)

def update_twin_state(alert_data, payload_size_kb):
    """
    This function represents the core logic of the Digital Twin.
    It receives an alert and updates its internal state, simulating the
    operation by writing the new state to a file.
    """
    sensor_id = alert_data.get("sensor_id", "unknown_sensor")
    alert_type = alert_data.get("alert_type", "GENERIC_ALERT")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    state_file_path = os.path.join(STATE_STORAGE_PATH, f"{sensor_id}.state")

    logger.info(f"--- DIGITAL TWIN STATE UPDATE ---")
    logger.info(f"Received alert '{alert_type}' ({payload_size_kb:.2f} KB) for component '{sensor_id}'.")
    logger.info("Updating internal state representation...")
    
    # Simulates a state update by appending the alert to a log file.
    try:
        with open(state_file_path, "a") as f:
            f.write(f"[{timestamp}] - {alert_type}: {json.dumps(alert_data)}\n")
        logger.info(f"State for '{sensor_id}' successfully persisted to {state_file_path}")
    except Exception as e:
        logger.error(f"Failed to persist state for {sensor_id}: {e}")
    logger.info(f"--- STATE UPDATE COMPLETE ---")

@app.route('/update', methods=['POST'])
def receive_alert():
    payload_size_kb = (request.content_length or 0) / 1024
    alert_payload = request.get_json(silent=True) or {}
    if not alert_payload:
        logger.warning("Received an empty update request.")
        return {"status": "empty_request"}, 400
    
    update_twin_state(alert_payload, payload_size_kb)
    
    return {"status": "twin_state_updated"}, 200

if __name__ == "__main__":
    logger.info("Digital Twin service starting...")
    logger.info(f"State storage is located at: {STATE_STORAGE_PATH}")
    app.run(host='0.0.0.0', port=5000)