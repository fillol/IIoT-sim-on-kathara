import random
from .base_sensor import IndustrialSensor

class TemperatureSensor(IndustrialSensor):
    def _generate_specific_data(self, target_size):
        return {
            "motor_temp": random.uniform(30.0, 90.0),
            "bearing_temp": random.uniform(25.0, 70.0),
            "coolant_temp": random.uniform(15.0, 45.0),
            "unit": "°C",
            "trend": [random.random() for _ in range(50)],
            "metadata": self._generate_metadata(target_size)
        }
    
    def _generate_metadata(self, size):
        return {"stability": random.choice(["stable", "fluctuating"]), "size": size}
