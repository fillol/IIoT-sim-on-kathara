import logging
import json
import os
import psutil
import requests
from flask import Flask, request
from cryptography.fernet import Fernet

# LOGGING
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)
logger = logging.getLogger("Decrypter")
app = Flask(__name__)

# URL of the next service in the pipeline for decrypted data.
FAULT_DETECTOR_URL = os.getenv("FAULT_DETECTOR_URL", "http://fault-detector:5000/data")

# MUST match the one used by the SecuritySensor
ENCRYPTION_KEY = b'u25A1N5g-jPAAZ_2CBl2i8o_HAG8AAnYq0_s2An1gE0='
cipher_suite = Fernet(ENCRYPTION_KEY)

@app.route('/decrypt', methods=['POST'])
def decrypt_and_forward():
    payload = request.get_json(silent=True)
    if not payload or "encrypted_payload" not in payload:
        logger.error("Invalid payload received. Missing 'encrypted_payload'.")
        return {"error": "Invalid payload"}, 400

    try:
        # Decryption
        logger.info("Received an encrypted payload. Attempting to decrypt...")
        encrypted_data = payload["encrypted_payload"].encode('utf-8')
        
        decrypted_bytes = cipher_suite.decrypt(encrypted_data)
        decrypted_payload = json.loads(decrypted_bytes.decode('utf-8'))
        
        sensor_id = decrypted_payload.get("sensor_id", "secure_N/A")
        logger.info(f"Payload from sensor {sensor_id} decrypted successfully.")

        # Forward the now-decrypted payload to the Fault Detector.
        try:
            logger.info(f"Forwarding decrypted payload for {sensor_id} to Fault Detector.")
            response = requests.post(FAULT_DETECTOR_URL, json=decrypted_payload, timeout=5)
            response.raise_for_status()
            logger.info(f"Successfully forwarded data for {sensor_id}. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to forward decrypted message to Fault Detector: {e}")
            return {"error": "Failed to forward after decryption"}, 502

    except Exception as e:
        logger.error(f"Decryption failed or error processing message: {e}", exc_info=True)
        return {"error": "Decryption failed"}, 500

    return {"status": "decrypted and forwarded"}, 200

if __name__ == "__main__":
    logger.info("Decrypter service starting as a Flask server...")
    app.run(host='0.0.0.0', port=5000)