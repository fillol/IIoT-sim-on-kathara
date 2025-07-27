import logging
import json
import os
import psutil
import requests
import coloredlogs
from flask import Flask, request
from cryptography.fernet import Fernet
from waitress import serve

# UNIFIED AND COLORED LOGGING CONFIGURATION
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
coloredlogs.install(level='INFO', fmt=LOG_FORMAT, isatty=True)
logger = logging.getLogger("Decrypter")
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

app = Flask(__name__)
process = psutil.Process(os.getpid())

# SERVICE CONFIGURATION
FAULT_DETECTOR_URL = os.getenv("FAULT_DETECTOR_URL", "http://fault-detector:5000/data")
ENCRYPTION_KEY = b'u25A1N5g-jPAAZ_2CBl2i8o_HAG8AAnYq0_s2An1gE0='
cipher_suite = Fernet(ENCRYPTION_KEY)

@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "ok"}, 200

@app.route('/decrypt', methods=['POST'])
def decrypt_and_forward():
    mem_before_kb = process.memory_info().rss / 1024

    payload = request.get_json(silent=True)
    if not payload or "encrypted_payload" not in payload:
        logger.error("Invalid payload received. Missing 'encrypted_payload'.")
        return {"error": "Invalid payload"}, 400

    try:
        logger.info("Received an encrypted payload. Attempting to decrypt...")
        encrypted_data = payload["encrypted_payload"].encode('utf-8')
        decrypted_bytes = cipher_suite.decrypt(encrypted_data)
        decrypted_payload = json.loads(decrypted_bytes.decode('utf-8'))
        sensor_id = decrypted_payload.get("sensor_id", "secure_N/A")
        logger.info(f"Payload from sensor {sensor_id} decrypted successfully.")

        try:
            logger.info(f"Forwarding decrypted payload for {sensor_id} to Fault Detector.")
            response = requests.post(FAULT_DETECTOR_URL, json=decrypted_payload, timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to forward decrypted message to Fault Detector: {e}")
            return {"error": "Failed to forward after decryption"}, 502

    except Exception as e:
        logger.error(f"Decryption failed: {e}", exc_info=False)
        return {"error": "Decryption failed"}, 500
    finally:
        mem_after_kb = process.memory_info().rss / 1024
        mem_diff_kb = mem_after_kb - mem_before_kb
        logger.info(f"Request processed. RAM usage delta: {mem_diff_kb:.4f} KB")

    return {"status": "decrypted and forwarded"}, 200

if __name__ == "__main__":
    logger.info("Service starting on port 5000...")
    serve(app, host='0.0.0.0', port=5000)