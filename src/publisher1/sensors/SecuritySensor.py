import random
import uuid
import json
from faker import Faker
from cryptography.fernet import Fernet
from .base_sensor import IndustrialSensor

fake = Faker()

ENCRYPTION_KEY = b'u25A1N5g-jPAAZ_2CBl2i8o_HAG8AAnYq0_s2An1gE0='
cipher_suite = Fernet(ENCRYPTION_KEY)

class SecuritySensor(IndustrialSensor):
    def _generate_specific_data(self, target_size):
        status_code = random.choice([200, 200, 200, 401, 403, 500])
        access_attempts = random.randint(0, 5) if status_code == 200 else random.randint(1, 10)

        data = {
            "event_id": str(uuid.uuid4()),
            "status_code": status_code,
            "description": f"Security check event. Status: {status_code}",
            "access_attempts": access_attempts,
            "source_ip": fake.ipv4(),
            "user_agent": fake.user_agent(),
            "criticality": "Low" if status_code == 200 else random.choice(["Medium", "High"])
        }
        return data

    def generate_payload(self):
        # This method is overridden to handle the encryption of the entire payload.
        # First, the standard payload is generated using the parent method.
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