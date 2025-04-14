
import asyncio
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
    payload_variation: str  # small/medium/large
    qos: int

class IndustrialSensor:
    def __init__(self, line_id, config):
        self.line_id = line_id
        self.config = config
        self.sensor_id = fake.uuid4()[:8]
        
    async def generate_payload(self):
            base = {
                "timestamp": datetime.utcnow().isoformat(),
                "line_id": self.line_id,
                "sensor_id": self.sensor_id,
                "type": self.config.sensor_type
            }
            
            # Modifica critica alla generazione della dimensione
            size = random.randint(*self._get_size_range(self.config.payload_variation))  # Sostituito random.choice con randint
            
            payload_data = {**base, **self._generate_specific_data(size)}
            
            # Calcola lo spazio mancante e aggiungi padding come campo
            json_base = json.dumps(payload_data)
            missing_bytes = max(0, size - len(json_base))
            
            full_payload = {
                **payload_data,
                "padding": "0" * missing_bytes
            }
            
            return json.dumps(full_payload)
    
    def _get_size_range(self, variation):
        return {
            "small": (1024, 10240),     # 1KB-10KB
            "medium": (10240, 102400),  # 10KB-100KB
            "large": (102400, 1048576)  # 100KB-1MB
        }[variation]
    
    def _generate_specific_data(self, target_size):
        # Implementato nelle classi figlie
        raise NotImplementedError
