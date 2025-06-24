import random
import json
from datetime import datetime
from dataclasses import dataclass
from faker import Faker

fake = Faker()

@dataclass
class SensorConfig:
    sensor_type: str
    update_interval: float
    payload_variation: str
    qos: int

class IndustrialSensor:
    def __init__(self, line_id, config):
        self.line_id = line_id
        self.config = config
        self.sensor_id = fake.uuid4()[:8]

    def generate_payload(self):
        # The payload generation is now clean, as the main computational
        # load is handled by the Digital Twin worker process.
        base = {
            "timestamp": datetime.utcnow().isoformat(),
            "line_id": self.line_id,
            "sensor_id": self.sensor_id,
            "type": self.config.sensor_type
        }
        
        size = random.randint(*self._get_size_range(self.config.payload_variation))
        payload_data = {**base, **self._generate_specific_data(size)}
        
        json_base = json.dumps(payload_data)
        missing_bytes = max(0, size - len(json_base))
        
        return json.dumps({**payload_data, "padding": "0" * missing_bytes})

    def _get_size_range(self, variation):
        return {"small": (1024, 10240), "medium": (10240, 102400), "large": (102400, 1048576)}[variation]

    def _generate_specific_data(self, target_size):
        raise NotImplementedError