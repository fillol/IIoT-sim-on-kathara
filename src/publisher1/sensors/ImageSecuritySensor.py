# src/publisher1/sensors/ImageSecuritySensor.py

import os
import random
import json
import base64
from PIL import Image
from faker import Faker
from cryptography.fernet import Fernet
from .base_sensor import IndustrialSensor

fake = Faker()

# The encryption key MUST match the one used by the decrypter service.
ENCRYPTION_KEY = b'u25A1N5g-jPAAZ_2CBl2i8o_HAG8AAnYq0_s2An1gE0='
cipher_suite = Fernet(ENCRYPTION_KEY)

# Path to the directory containing images to be sent.
IMAGE_SOURCE_DIR = "/app/images"

class ImageSecuritySensor(IndustrialSensor):
    """
    A specialized security sensor that captures, encodes, and encrypts image data.
    This simulates a visual inspection system where raw image data must be
    securely transmitted for centralized analysis.
    """
    def __init__(self, line_id, config):
        super().__init__(line_id, config)
        # Load the list of available images at startup.
        self.available_images = self._load_image_paths()
        if not self.available_images:
            # Log an error if no images are found to send.
            print(f"ERROR: No images found in {IMAGE_SOURCE_DIR} for ImageSecuritySensor.")

    def _load_image_paths(self):
        """Scans the image directory and returns a list of valid image file paths."""
        if not os.path.exists(IMAGE_SOURCE_DIR):
            return []
        return [os.path.join(IMAGE_SOURCE_DIR, f) for f in os.listdir(IMAGE_SOURCE_DIR)
                if os.path.isfile(os.path.join(IMAGE_SOURCE_DIR, f))]

    def _generate_specific_data(self, target_size):
        """
        Overrides the base method to provide image-specific data.
        It selects a random image, encodes it in Base64, and prepares it for the payload.
        """
        if not self.available_images:
            return {"error": "no_images_available", "image_data": ""}

        # Select a random image from the available list for each payload.
        image_path = random.choice(self.available_images)
        image_filename = os.path.basename(image_path)

        try:
            # Open the image and convert it to bytes, then encode in Base64.
            # Base64 is used to safely embed binary data within a JSON text payload.
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
                encoded_string = base64.b64encode(image_bytes).decode('utf-8')

            return {
                "image_filename": image_filename,
                "image_data": encoded_string,  # The core data payload.
                "event_type": "visual_anomaly_check",
                "operator": fake.name()
            }
        except Exception as e:
            # Handle potential file reading or encoding errors.
            print(f"ERROR: Could not read or encode image {image_path}: {e}")
            return {"error": "image_processing_failed", "image_data": ""}

    def generate_payload(self):
        """
        This method is overridden to handle the encryption of the entire payload.
        The process is similar to the standard SecuritySensor, but the underlying
        data now contains a Base64 encoded image, resulting in a much larger payload.
        """
        # The 'type' is explicitly set here to be used by the fault-detector for routing.
        self.config.sensor_type = "image_security"
        base_payload_str = super().generate_payload()
        
        try:
            # The full JSON payload is encrypted using Fernet symmetric encryption.
            payload_bytes = base_payload_str.encode('utf-8')
            encrypted_payload = cipher_suite.encrypt(payload_bytes)
            
            # A new wrapper payload is created to be sent over the network.
            wrapper_payload = {
                "encrypted_payload": encrypted_payload.decode('utf-8'),
                "source": "secure"
            }
            
            return json.dumps(wrapper_payload)
            
        except Exception as e:
            # Fallback in case of an encryption error.
            return json.dumps({"error": "encryption_failed", "details": str(e)})