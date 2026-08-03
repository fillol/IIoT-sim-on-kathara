import random
from faker import Faker
from .base_sensor import IndustrialSensor

fake = Faker()

class QualitySensor(IndustrialSensor):
    def _generate_specific_data(self, target_size):
        return {
            "defect_count": random.randint(0, 5),
            "defect_types": random.sample(["scratch", "dent", "misalignment"], random.randint(0,2)),
            "image_meta": {
                "hash": fake.sha256(),
                "size_kb": target_size//1024,
                "defect_coordinates": [(random.randint(0,1000), random.randint(0,1000)) for _ in range(3)]
            },
            "operator": fake.name(),
            "batch_id": fake.bothify("BATCH-####-???")
        }
