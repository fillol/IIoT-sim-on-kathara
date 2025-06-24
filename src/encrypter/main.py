import logging
import json
import base64
import os
import psutil
import requests
from flask import Flask, request

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Encrypter")

app = Flask(__name__)
process = psutil.Process(os.getpid())

# The Control Center URL now points to the secure interface
CONTROL_CENTER_URL = "http://10.4.4.2:5000/data"

@app.route('/encrypt', methods=['POST'])
def encrypt_and_forward():
    """
    Endpoint to receive data, encrypt it, and forward to the Control Center.
    """
    mem_before = process.memory_info().rss / (1024 * 1024)
    
    original_payload_dict = request.get_json()
    if not original_payload_dict:
        return {"error": "Invalid JSON"}, 400

    try:
        # Encryption logic is the same as before
        original_payload_str = json.dumps(original_payload_dict)
        encoded_payload_str = base64.b64encode(original_payload_str.encode('utf-8')).decode('utf-8')

        republish_payload = {
            "encrypted_payload": encoded_payload_str,
            "source": "secure",
        }

        # Instead of publishing to MQTT, we POST to the control center
        response = requests.post(CONTROL_CENTER_URL, json=republish_payload, timeout=5)
        response.raise_for_status() # Raise an exception for 4xx/5xx status codes
        
        logger.info(f"Encrypted message forwarded to Control Center, status: {response.status_code}")

        mem_after = process.memory_info().rss / (1024 * 1024)
        logger.info(f"Encryption and forwarding complete. RAM usage: {mem_after - mem_before:.6f} MB")

        return {"status": "encrypted and forwarded"}, 200

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to forward message to Control Center: {e}")
        return {"error": "Failed to forward to control center"}, 502
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return {"error": "Internal server error"}, 500

if __name__ == "__main__":
    logger.info("Encrypter service starting as a Flask server...")
    app.run(host='0.0.0.0', port=5000)