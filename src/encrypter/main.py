import logging
import json
import base64
import os
import psutil
import requests
from flask import Flask, request

# --- UNIFIED LOGGING CONFIGURATION ---
# Define a clean, consistent log format for all services
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# Silence the default Flask logger to reduce noise and avoid duplicate logs
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

logger = logging.getLogger("Encrypter")
app = Flask(__name__)
process = psutil.Process(os.getpid())
CONTROL_CENTER_URL = "http://10.4.4.2:5000/data"


@app.route('/encrypt', methods=['POST'])
def encrypt_and_forward():
    # Measure RAM in Kilobytes for better precision
    mem_before_kb = process.memory_info().rss / 1024

    original_payload_dict = request.get_json(silent=True)
    if not original_payload_dict:
        return {"error": "Invalid JSON"}, 400

    try:
        original_payload_str = json.dumps(original_payload_dict)
        encoded_payload_str = base64.b64encode(original_payload_str.encode('utf-8')).decode('utf-8')
        republish_payload = {"encrypted_payload": encoded_payload_str, "source": "secure"}

        # Forward the encrypted payload to the Control Center
        response = requests.post(CONTROL_CENTER_URL, json=republish_payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Encrypted message forwarded to CC, status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to forward message to Control Center: {e}")
        return {"error": "Failed to forward"}, 502
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return {"error": "Internal error"}, 500
    
    finally:
        mem_after_kb = process.memory_info().rss / 1024
        mem_diff_kb = mem_after_kb - mem_before_kb
        # Log with high precision to see small changes
        logger.info(f"Request finished. RAM usage: {mem_diff_kb:.4f} KB")

    return {"status": "encrypted and forwarded"}, 200


if __name__ == "__main__":
    logger.info("Encrypter service starting as a Flask server...")
    app.run(host='0.0.0.0', port=5000)