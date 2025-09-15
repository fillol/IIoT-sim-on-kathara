import logging
import warnings
import json
import os
import psutil
import requests
from flask import Flask, request
import numpy as np
import joblib
import base64
import io
from PIL import Image, ImageFilter

# LOGGING
warnings.filterwarnings("ignore", category=DeprecationWarning)
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)
logger = logging.getLogger("FaultDetector")

app = Flask(__name__)

DIGITAL_TWIN_URL = os.getenv("DIGITAL_TWIN_URL", "http://10.7.0.2:5000/update")

try:
    RAM_LOAD_MB = 1024
    logger.info(f"Simulating RAM load: allocating a {RAM_LOAD_MB}MB numpy array...")
    num_elements = (RAM_LOAD_MB * 1024 * 1024) // 8
    REFERENCE_DATASET = np.random.rand(num_elements)
    logger.info("RAM load simulation complete. Memory allocated.")
except Exception as e:
    logger.error(f"Failed to allocate memory for RAM load simulation: {e}")
    REFERENCE_DATASET = None

try:
    CLASSIFIER_MODEL = joblib.load('pickle_model.pkl')
    logger.info("Image classification model 'pickle_model.pkl' loaded successfully.")
except FileNotFoundError:
    logger.error("FATAL: Classification model 'pickle_model.pkl' not found. Image analysis will fail.")
    CLASSIFIER_MODEL = None

CLASSIFICATION_NAMEMAP = [
    'axes', 'boots', 'carabiners', 'crampons', 'gloves', 'hardshell_jackets',
    'harnesses', 'helmets', 'insulated_jackets', 'pulleys', 'rope', 'tents'
]
UNAUTHORIZED_OBJECTS = {'axes', 'crampons', 'pulleys'}

def resize(image):
    """Resizes an image to fit within a fixed 128x128 canvas, maintaining aspect ratio."""
    base = 128
    newImage = Image.new('RGB', (base, base), (255, 255, 255))
    img_copy = image.copy()
    img_copy.thumbnail((base, base), Image.ANTIALIAS)
    position_x = (base - img_copy.width) // 2
    position_y = (base - img_copy.height) // 2
    newImage.paste(img_copy, (position_x, position_y))
    return newImage

def normalize(arr):
    """Normalizes the pixel values of an image array to a scale of 0-255."""
    arr = arr.astype('float')
    for i in range(3):
        minval = arr[..., i].min()
        maxval = arr[..., i].max()
        if minval != maxval:
            arr[..., i] -= minval
            arr[..., i] *= (255.0 / (maxval - minval))
    return arr

def intensive_feature_extraction(image):
    """
    Simulates a more complex feature extraction process typical of deep learning models.
    Applies a series of convolution filters to the image, which is a CPU-intensive task.
    """
    logger.info("Performing intensive feature extraction...")
    rgb_image = image.convert("RGB")
    processed_image = rgb_image.filter(ImageFilter.FIND_EDGES)
    processed_image = processed_image.filter(ImageFilter.GaussianBlur(radius=2))
    processed_image = processed_image.filter(ImageFilter.CONTOUR)
    
    logger.info("Intensive feature extraction complete.")
    return processed_image

def forward_alert_to_digital_twin(alert_payload):
    """Forwards a detected alert to the Digital Twin service for state update."""
    try:
        sensor_id = alert_payload.get('sensor_id', 'unknown')
        alert_size_kb = len(json.dumps(alert_payload).encode('utf-8')) / 1024
        logger.info(f"Forwarding alert ({alert_size_kb:.2f} KB) for sensor {sensor_id} to Digital Twin.")
        requests.post(DIGITAL_TWIN_URL, json=alert_payload, timeout=5)
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not forward alert to Digital Twin: {e}")

def process_message(payload_dict, payload_size_kb):
    """
    Core business logic. Now includes artificial load for image processing.
    """
    try:
        sensor_id = payload_dict.get("sensor_id", "N/A")
        line_id = payload_dict.get("line_id", "N/A")
        sensor_type = payload_dict.get("type")
        
        logger.info(f"Analyzing data ({payload_size_kb:.2f} KB) from {line_id}/{sensor_id} (type: {sensor_type}).")
        
        if sensor_type == "image_security":
            if not CLASSIFIER_MODEL:
                logger.error(f"Cannot process image from {sensor_id}: Model not loaded.")
                return
            
            image_data_b64 = payload_dict.get("image_data")
            if not image_data_b64:
                logger.warning(f"Received image_security payload from {sensor_id} with no image data.")
                return
            
            image_bytes = base64.b64decode(image_data_b64)
            image = Image.open(io.BytesIO(image_bytes))

            # 1. Simulate complex feature extraction (heavy on CPU).
            #    This operation is performed on the high-resolution image.
            _ = intensive_feature_extraction(image)
            
            # 2. Pre-process the image for the model (resize and normalize).
            processed_image = resize(image)
            normalized_array = normalize(np.array(processed_image))
            image_features = normalized_array.ravel().reshape(1, -1)

            # 3. Perform prediction.
            prediction_result = CLASSIFIER_MODEL.predict(image_features)
            predicted_class_name = CLASSIFICATION_NAMEMAP[int(prediction_result[0])]
            logger.info(f"Image from {sensor_id} classified as: '{predicted_class_name}'.")

            # 4. Check for alerts.
            if predicted_class_name in UNAUTHORIZED_OBJECTS:
                alert = {
                    **payload_dict, 
                    "image_data": "omitted_for_alert",
                    "alert_type": "Unauthorized Object Detected", 
                    "message": f"Unauthorized object '{predicted_class_name}' detected by {sensor_id} on line {line_id}!"
                }
                logger.critical(alert["message"])
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
    payload_size_kb = (request.content_length or 0) / 1024
    payload = request.get_json(silent=True) or {}
    process_message(payload, payload_size_kb)
    return {"status": "analysis complete"}, 200

if __name__ == "__main__":
    logger.info("Fault Detection service starting...")
    app.run(host='0.0.0.0', port=5000)