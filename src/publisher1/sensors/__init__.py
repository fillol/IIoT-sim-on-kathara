from .base_sensor import SensorConfig, IndustrialSensor
from .VibrationSensor import VibrationSensor
from .TemperatureSensor import TemperatureSensor
from .QualitySensor import QualitySensor
from .SecuritySensor import SecuritySensor # Import the new sensor

all = [
    'SensorConfig',
    'IndustrialSensor',
    'VibrationSensor',
    'TemperatureSensor',
    'QualitySensor',
    'SecuritySensor'
]