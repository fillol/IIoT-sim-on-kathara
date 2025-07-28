import logging
import json
import os
import psutil
import requests
from flask import Flask, request

# LOGGING
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)
logger = logging.getLogger("FaultDetector")

app = Flask(__name__)

# URL of the Digital Twin service, which receives detected alerts.
DIGITAL_TWIN_URL = os.getenv("DIGITAL_TWIN_URL", "http://10.7.0.2:5000/update")

def forward_alert_to_digital_twin(alert_payload):
    """Forwards a detected alert to the Digital Twin service for state update."""
    try:
        sensor_id = alert_payload.get('sensor_id', 'unknown')
        logger.info(f"Forwarding alert for sensor {sensor_id} to Digital Twin.")
        requests.post(DIGITAL_TWIN_URL, json=alert_payload, timeout=5)
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not forward alert to Digital Twin: {e}")

def process_message(payload_dict):
    """
    This is the core business logic for analyzing sensor data and detecting faults.
    It receives only clear-text data (standard or decrypted).
    """
    try:
        sensor_id = payload_dict.get("sensor_id", "N/A")
        line_id = payload_dict.get("line_id", "N/A")
        sensor_type = payload_dict.get("type")
        
        logger.info(f"Analyzing data from {line_id}/{sensor_id} (type: {sensor_type}).")
        
        # Rule set for decrypted security data.
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

        # Rule set for standard industrial sensor data.
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
        logger.error(f"Error processing message in fault detector: {e}", exc_info=True)


@app.route('/data', methods=['POST'])
def receive_data():
    payload = request.get_json(silent=True) or {}
    process_message(payload)
    return {"status": "analysis complete"}, 200

if __name__ == "__main__":
    logger.info("Fault Detection service starting...")
    app.run(host='0.0.0.0', port=5000)