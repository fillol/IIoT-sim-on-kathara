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
        base_payload = super().generate_payload()
        
        try:
            payload_bytes = base_payload.encode('utf-8')
            encrypted_payload = cipher_suite.encrypt(payload_bytes)
            
            wrapper_payload = {
                "encrypted_payload": encrypted_payload.decode('utf-8'),
                "source": "secure"
            }
            
            print(f"DEBUG: Sensor {self.sensor_id} has encrypted a payload.")

            return json.dumps(wrapper_payload)
            
        except Exception as e:
            print(f"ERROR: Could not encrypt payload: {e}")

            return json.dumps({"error": "encryption_failed"})