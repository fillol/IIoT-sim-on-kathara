import logging
import json
import os
import psutil
import requests
import numpy as np
from flask import Flask, request

# LOGGING
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)
logger = logging.getLogger("Dropper")

app = Flask(__name__)

# The lambda parameter for the Poisson distribution determines the drop rate.
# A lambda of 0.1 means that, on average, about 9.5% of packets will be dropped.
POISSON_LAMBDA = float(os.getenv("POISSON_LAMBDA", "0.1"))

# Downstream service URLs are retrieved from environment variables for flexibility.
DECRYPTER_URL = os.getenv("DECRYPTER_URL", "http://decrypter:5000/decrypt")
FAULT_DETECTOR_URL = os.getenv("FAULT_DETECTOR_URL", "http://fault-detector:5000/data")

@app.route('/data', methods=['POST'])
def route_or_drop():
    # A random value from a Poisson distribution is used to simulate packet loss.
    # If the value is greater than 0, the packet is "dropped".
    if np.random.poisson(lam=POISSON_LAMBDA) > 0:
        logger.warning("SIMULATING PACKET LOSS: Message dropped based on Poisson distribution.")
        # We return a 200 OK to the client to simulate a packet lost in transit,
        # where the client believes the send was successful.
        return {"status": "dropped"}, 200

    payload = request.get_json(silent=True)
    if not payload:
        return {"error": "Invalid JSON"}, 400

    # The service inspects the payload to decide the correct route.
    # If the 'source' key is 'secure', it forwards to the Decrypter service.
    # Otherwise, it forwards directly to the Fault Detector.
    is_secure = payload.get("source") == "secure"
    target_url = DECRYPTER_URL if is_secure else FAULT_DETECTOR_URL
    log_prefix = "[SECURE -> DECRYPTER]" if is_secure else "[STANDARD -> FAULT-DETECTOR]"

    try:
        logger.info(f"{log_prefix} Forwarding message to {target_url}...")
        response = requests.post(target_url, json=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Message forwarded successfully. Downstream service responded with {response.status_code}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to forward message to {target_url}: {e}")
        return {"error": "Failed to forward"}, 502

    return {"status": "forwarded"}, 200

if __name__ == "__main__":
    logger.info(f"Dropper service starting... Packet drop rate (Poisson lambda) is {POISSON_LAMBDA}.")
    app.run(host='0.0.0.0', port=5000)