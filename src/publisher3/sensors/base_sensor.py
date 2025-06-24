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

    def _dummy_computation(self):
        # This computation creates a memory-heavy object.
        list_size = 30000 # Increased size for undeniable impact
        dummy_list = [random.random() for _ in range(list_size)]
        # We now return the list itself to keep it in memory.
        return dummy_list

    def generate_payload(self):
        base = {
            "timestamp": datetime.utcnow().isoformat(),
            "line_id": self.line_id,
            "sensor_id": self.sensor_id,
            "type": self.config.sensor_type
        }
        
        dummy_list = self._dummy_computation()

        size = random.randint(*self._get_size_range(self.config.payload_variation))
        # The content of the dummy list is not important, just its existence.
        payload_data = {**base, **self._generate_specific_data(size), "dummy_check": len(dummy_list)}
        
        json_base = json.dumps(payload_data)
        missing_bytes = max(0, size - len(json_base))
        
        payload_str = json.dumps({**payload_data, "padding": "0" * missing_bytes})
        
        # Return both the payload and the list that consumes memory
        return payload_str, dummy_list

    def _get_size_range(self, variation):
        return {"small": (1024, 10240), "medium": (10240, 102400), "large": (102400, 1048576)}[variation]

    def _generate_specific_data(self, target_size):
        raise NotImplementedError