import logging
import json
import os
import psutil
import requests
import numpy as np
import coloredlogs
from flask import Flask, request
from waitress import serve

# UNIFIED AND COLORED LOGGING CONFIGURATION
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
coloredlogs.install(level='INFO', fmt=LOG_FORMAT, isatty=True)
logger = logging.getLogger("Dropper")
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)

app = Flask(__name__)
process = psutil.Process(os.getpid())

# SERVICE CONFIGURATION
POISSON_LAMBDA = float(os.getenv("POISSON_LAMBDA", "0.1"))
DECRYPTER_URL = os.getenv("DECRYPTER_URL", "http://decrypter:5000/decrypt")
FAULT_DETECTOR_URL = os.getenv("FAULT_DETECTOR_URL", "http://fault-detector:5000/data")

@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "ok"}, 200

@app.route('/data', methods=['POST'])
def route_or_drop():
    mem_before_kb = process.memory_info().rss / 1024

    if np.random.poisson(lam=POISSON_LAMBDA) > 0:
        logger.warning("SIMULATING PACKET LOSS: Message dropped based on Poisson distribution.")
        return {"status": "dropped"}, 200

    payload = request.get_json(silent=True)
    if not payload:
        return {"error": "Invalid JSON"}, 400

    is_secure = payload.get("source") == "secure"
    target_url = DECRYPTER_URL if is_secure else FAULT_DETECTOR_URL
    log_prefix = "[SECURE -> DECRYPTER]" if is_secure else "[STANDARD -> FAULT-DETECTOR]"

    try:
        logger.info(f"{log_prefix} Forwarding message...")
        response = requests.post(target_url, json=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"Message forwarded successfully to {target_url}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to forward message to {target_url}: {e}")
        return {"error": "Failed to forward"}, 502
    finally:
        mem_after_kb = process.memory_info().rss / 1024
        mem_diff_kb = mem_after_kb - mem_before_kb
        logger.info(f"Request processed. RAM usage delta: {mem_diff_kb:.4f} KB")

    return {"status": "forwarded"}, 200

if __name__ == "__main__":
    logger.info(f"Service starting on port 5000 with drop rate (Poisson lambda) = {POISSON_LAMBDA}.")
    serve(app, host='0.0.0.0', port=5000)