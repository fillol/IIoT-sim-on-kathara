import random
from .base_sensor import IndustrialSensor

class VibrationSensor(IndustrialSensor):
    def _generate_specific_data(self, target_size):
        return {
            "x": random.uniform(2.0, 15.0),
            "y": random.uniform(2.0, 15.0),
            "z": random.uniform(2.0, 15.0),
            "unit": "mm/s",
            "fft": [random.random() for _ in range(100)],
            "metadata": self._generate_metadata(target_size)
        }
    
    def _generate_metadata(self, size):
        return {"analysis": "spectral", "samples": size//1000}
