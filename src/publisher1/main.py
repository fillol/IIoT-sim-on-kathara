import json
import os
import logging
import time
import requests
import psutil
from sensors.base_sensor import SensorConfig
from sensors import VibrationSensor, TemperatureSensor, QualitySensor, SecuritySensor

# UNIFIED LOGGING CONFIGURATION
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("Producer")

# All publishers send data to a single entry point: the Dropper service.
# This service is responsible for simulating network issues and routing traffic.
DROPPER_URL = os.getenv("DROPPER_URL", "http://10.2.0.2:5000/data")
CONFIG_FILE_DIR = os.getenv("CONFIG_FILE_DIR", ".")


class ProductionLine:
    def __init__(self, config_file_path):
        with open(config_file_path) as f:
            self.config = json.load(f)
        self.sensors = self._init_sensors()
        self.process = psutil.Process(os.getpid())

    def _init_sensors(self):
        sensors = []
        # The sensor map dynamically loads the correct sensor class based on config.
        smap = {"vibration": VibrationSensor, "temperature": TemperatureSensor, "quality": QualitySensor, "security": SecuritySensor}
        for cfg in self.config.get("sensors", []):
            s_class = smap.get(cfg.get("type"))
            if s_class:
                sensors.append((s_class(self.config["line_id"], SensorConfig(cfg["type"], float(cfg["interval"]), cfg["payload"], int(cfg.get("qos",1)))), cfg))
        return sensors

    def run(self):
        logger.info(f"Starting REST producer for line {self.config.get('line_id', 'N/A')}")
        while True:
            for sensor, config in self.sensors:
                self.send_data(sensor, config)

    def send_data(self, sensor, config):
        mem_before_kb = self.process.memory_info().rss / 1024
        
        payload_str = sensor.generate_payload()
        payload_dict = json.loads(payload_str)
        
        try:
            # All data, secure or not, is sent to the Dropper service.
            response = requests.post(DROPPER_URL, json=payload_dict, timeout=10)
            response.raise_for_status()

            mem_after_kb = self.process.memory_info().rss / 1024
            mem_diff_kb = mem_after_kb - mem_before_kb
            
            # Determine sensor type for logging purposes.
            sensor_type_log = "secure" if "encrypted_payload" in payload_dict else payload_dict.get("type", "N/A")
            logger.info(f"Sensor type '{sensor_type_log}' published data via Dropper. RAM usage: {mem_diff_kb:.4f} KB")

        except requests.exceptions.RequestException as e:
            sensor_id_log = "N/A"
            if "encrypted_payload" not in payload_dict:
                 sensor_id_log = payload_dict.get("sensor_id", "N/A")
            logger.error(f"Sensor {sensor_id_log} failed to send data to {DROPPER_URL}: {e}")
        
        time.sleep(config.get("interval", 1.0))


if __name__ == "__main__":
    config_path = os.path.join(CONFIG_FILE_DIR, "line1.json")
    
    try:
        ProductionLine(config_path).run()
    except Exception as e:
        logger.critical(f"Failed to run production line from {config_path}: {e}", exc_info=True)