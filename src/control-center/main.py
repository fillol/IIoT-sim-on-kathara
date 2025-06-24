import logging
import json
import base64
import os
import psutil
from flask import Flask, request

# --- UNIFIED LOGGING CONFIGURATION ---
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

logger = logging.getLogger("ControlCenter")
app = Flask(__name__)
process = psutil.Process(os.getpid())


def process_message(payload_dict):
    """
    Business logic for processing a payload.
    """
    try:
        # Check for encrypted messages
        if payload_dict.get("source") == "secure" and "encrypted_payload" in payload_dict:
            try:
                encrypted_data = payload_dict["encrypted_payload"]
                decoded_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
                decrypted_data = json.loads(decoded_bytes.decode('utf-8'))
                sensor_id = decrypted_data.get("sensor_id", "secure_N/A")
                status_code = decrypted_data.get("status_code")
                
                logger.info(f"Received SECURE message via REST from sensor {sensor_id}")
                
                if status_code in [401, 403]:
                    logger.warning(f"[Encrypted] Access issue detected on {sensor_id}! Status: {status_code}")
                elif status_code == 500:
                    logger.warning(f"[Encrypted] Internal error reported by {sensor_id}! Status: {status_code}")

            except Exception as e:
                logger.error(f"Failed to decode or parse secure payload: {e}")
            return

        # For standard messages, extract sensor_id directly
        sensor_id = payload_dict.get("sensor_id", "N/A")
        line_id = payload_dict.get("line_id", "N/A")
        size_kb = len(str(payload_dict)) // 1024
        
        logger.info(f"Received standard message ({size_kb}KB) from {line_id}/{sensor_id}")
        sensor_type = payload_dict.get("type")

        # Add sensor_id to alert messages for clarity
        if sensor_type == "vibration" and payload_dict.get('x', 0) > 8.0:
            logger.warning(f"High vibration on {line_id}/{sensor_id}! Value: {payload_dict.get('x', 0):.2f} mm/s")
        elif sensor_type == "quality" and payload_dict.get('defect_count', 0) > 3:
            logger.error(f"Quality alert on {line_id}/{sensor_id}! {payload_dict.get('defect_count', 0)} defects detected.")
        elif sensor_type == "temperature" and payload_dict.get('motor_temp', 0) > 85.0:
            logger.warning(f"High temperature on {line_id}/{sensor_id}! Value: {payload_dict.get('motor_temp', 0):.1f}°C")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)


@app.route('/data', methods=['POST'])
def receive_data():
    mem_before_kb = process.memory_info().rss / 1024

    payload = request.get_json(silent=True) or {}
    process_message(payload)

    mem_after_kb = process.memory_info().rss / 1024
    mem_diff_kb = mem_after_kb - mem_before_kb
    
    logger.info(f"Request processed. RAM usage: {mem_diff_kb:.4f} KB")
    return {"status": "received"}, 200


if __name__ == "__main__":
    logger.info("Control Center starting as a Flask server...")
    app.run(host='0.0.0.0', port=5000)