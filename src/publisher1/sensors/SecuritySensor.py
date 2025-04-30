import random
import uuid
from faker import Faker # Importa Faker
from .base_sensor import IndustrialSensor

fake = Faker()

class SecuritySensor(IndustrialSensor):
    def _generate_specific_data(self, target_size):
        status_code = random.choice([200, 200, 200, 401, 403, 500])
        access_attempts = random.randint(0, 5) if status_code == 200 else random.randint(1, 10)

        data = {
            "event_id": str(uuid.uuid4()),
            "status_code": status_code,
            "description": f"Security check event. Status: {status_code}",
            "access_attempts": access_attempts,
            "source_ip": fake.ipv4(), # IP sorgente fittizio
            "user_agent": fake.user_agent(), # User agent fittizio
            "criticality": "Low" if status_code == 200 else random.choice(["Medium", "High"])
        }
        return data
