import logging
import json
import base64
import os
import psutil
from flask import Flask, request

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ControlCenter")

app = Flask(__name__)
process = psutil.Process(os.getpid())

def process_message(payload_dict):
    """
    Business logic for processing a payload, extracted for reusability.
    This was previously the body of the on_message callback.
    """
    try:
        # Check if it's an encrypted message from the encrypter service
        if payload_dict.get("source") == "secure" and "encrypted_payload" in payload_dict:
            logger.info("Received SECURE message via REST")

            try:
                encrypted_data = payload_dict["encrypted_payload"]
                decoded_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
                decrypted_payload_str = decoded_bytes.decode('utf-8')
                decrypted_data = json.loads(decrypted_payload_str)

                status_code = decrypted_data.get("status_code")
                # Alerting logic for security data remains the same
                if status_code in [401, 403]:
                    logger.warning(f"[Encrypted] Access issue detected! Status: {status_code}")
                elif status_code == 500:
                    logger.warning(f"[Encrypted] Internal error reported! Status: {status_code}")

            except (base64.binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.error(f"Failed to decode or parse secure payload: {e}")
            return

        size_kb = len(str(payload_dict)) // 1024
        logger.info(f"Received standard message ({size_kb}KB) via REST")
        sensor_type = payload_dict.get("type")

        if sensor_type == "vibration":
            vibration_x = payload_dict.get('x', 0)
            if isinstance(vibration_x, (int, float)) and vibration_x > 8.0:
                logger.warning(f"High vibration detected! Value: {vibration_x:.2f} mm/s")

        elif sensor_type == "quality":
             defect_count = payload_dict.get('defect_count', 0)
             if isinstance(defect_count, int) and defect_count > 3:
                logger.error(f"Quality alert! {defect_count} defects detected.")

        elif sensor_type == "temperature":
             temp_c = payload_dict.get('motor_temp', 0)
             if isinstance(temp_c, (int, float)) and temp_c > 85.0:
                 logger.warning(f"High temperature detected! Value: {temp_c:.1f}°C")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)

@app.route('/data', methods=['POST'])
def receive_data():
    """
    REST endpoint to receive data from producers or the encrypter.
    """
    mem_before = process.memory_info().rss / (1024 * 1024)
    
    payload = request.get_json()
    if not payload:
        return {"error": "Invalid JSON"}, 400
    
    process_message(payload)
    
    mem_after = process.memory_info().rss / (1024 * 1024)
    logger.info(f"Request processed. RAM usage for this operation: {mem_after - mem_before:.6f} MB")
    
    return {"status": "received"}, 200

if __name__ == "__main__":
    logger.info("Control Center starting as a Flask server...")
    app.run(host='0.0.0.0', port=5000)