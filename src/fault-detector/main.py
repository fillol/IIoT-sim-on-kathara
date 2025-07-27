import logging
import json
import os
import psutil
import requests
import coloredlogs
from flask import Flask, request
from waitress import serve

# UNIFIED AND COLORED LOGGING CONFIGURATION
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
coloredlogs.install(level='INFO', fmt=LOG_FORMAT, isatty=True)
logger = logging.getLogger("FaultDetector")
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

app = Flask(__name__)
process = psutil.Process(os.getpid())

# SERVICE CONFIGURATION
DIGITAL_TWIN_URL = os.getenv("DIGITAL_TWIN_URL", "http://digital-twin:5000/update")

def forward_alert_to_digital_twin(alert_payload):
    try:
        sensor_id = alert_payload.get('sensor_id', 'unknown')
        logger.info(f"Forwarding alert for sensor {sensor_id} to Digital Twin.")
        requests.post(DIGITAL_TWIN_URL, json=alert_payload, timeout=5)
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not forward alert to Digital Twin: {e}")

def process_message(payload_dict):
    try:
        sensor_id = payload_dict.get("sensor_id", "N/A")
        line_id = payload_dict.get("line_id", "N/A")
        sensor_type = payload_dict.get("type")
        logger.info(f"Analyzing data from {line_id}/{sensor_id} (type: {sensor_type}).")

        if "status_code" in payload_dict:
            status_code = payload_dict.get("status_code")
            if status_code in [401, 403]:
                alert = {**payload_dict, "alert_type": "Security Breach", "message": f"Access issue detected on {sensor_id}! Status: {status_code}"}
                logger.warning(alert["message"])
                forward_alert_to_digital_twin(alert)
            elif status_code == 500:
                alert = {**payload_dict, "alert_type": "Security System Error", "message": f"Internal error reported by security sensor {sensor_id}! Status: {status_code}"}
                logger.warning(alert["message"])
                forward_alert_to_digital_twin(alert)
            return

        if sensor_type == "vibration" and payload_dict.get('x', 0) > 8.0:
            alert = {**payload_dict, "alert_type": "High Vibration", "message": f"High vibration on {line_id}/{sensor_id}! Value: {payload_dict.get('x', 0):.2f} mm/s"}
            logger.warning(alert["message"])
            forward_alert_to_digital_twin(alert)
        elif sensor_type == "quality" and payload_dict.get('defect_count', 0) > 3:
            alert = {**payload_dict, "alert_type": "Quality Alert", "message": f"Quality alert on {line_id}/{sensor_id}! {payload_dict.get('defect_count', 0)} defects detected."}
            logger.error(alert["message"])
            forward_alert_to_digital_twin(alert)
        elif sensor_type == "temperature" and payload_dict.get('motor_temp', 0) > 85.0:
            alert = {**payload_dict, "alert_type": "High Temperature", "message": f"High temperature on {line_id}/{sensor_id}! Value: {payload_dict.get('motor_temp', 0):.1f}°C"}
            logger.warning(alert["message"])
            forward_alert_to_digital_twin(alert)
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)

@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "ok"}, 200

@app.route('/data', methods=['POST'])
def receive_data():
    mem_before_kb = process.memory_info().rss / 1024
    payload = request.get_json(silent=True) or {}
    process_message(payload)
    mem_after_kb = process.memory_info().rss / 1024
    mem_diff_kb = mem_after_kb - mem_before_kb
    logger.info(f"Analysis complete. RAM usage delta: {mem_diff_kb:.4f} KB")
    return {"status": "analysis complete"}, 200

if __name__ == "__main__":
    logger.info("Service starting on port 5000...")
    serve(app, host='0.0.0.0', port=5000)