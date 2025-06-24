import json
import os
import logging
import time
import requests
import psutil
from sensors.base_sensor import SensorConfig
from sensors import VibrationSensor, TemperatureSensor, QualitySensor, SecuritySensor

# --- UNIFIED LOGGING CONFIGURATION ---
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("Producer")

CONTROL_CENTER_URL = os.getenv("CC_URL", "http://10.3.4.2:5000/data")
ENCRYPTER_URL = os.getenv("ENCRYPTER_URL", "http://10.2.1.2:5000/encrypt")
CONFIG_FILE_DIR = os.getenv("CONFIG_FILE_DIR", ".")


class ProductionLine:
    def __init__(self, config_file_path):
        with open(config_file_path) as f:
            self.config = json.load(f)
        self.sensors = self._init_sensors()
        self.process = psutil.Process(os.getpid())

    def _init_sensors(self):
        sensors = []
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
            time.sleep(0.1)

    def send_data(self, sensor, config):
        mem_before_kb = self.process.memory_info().rss / 1024
        
        payload_str = sensor.generate_payload()
        payload_dict = json.loads(payload_str)
        size_kb = len(payload_str) // 1024
        
        # Extract sensor_id for better logging
        sensor_id = payload_dict.get("sensor_id", "N/A")

        is_secure = sensor.config.sensor_type == "security"
        target_url = ENCRYPTER_URL if is_secure else CONTROL_CENTER_URL
        log_prefix = "[SECURE]" if is_secure else "[STANDARD]"

        try:
            response = requests.post(target_url, json=payload_dict, timeout=10)
            response.raise_for_status()

            mem_after_kb = self.process.memory_info().rss / 1024
            mem_diff_kb = mem_after_kb - mem_before_kb
            # Added sensor_id to the log message
            logger.info(f"{log_prefix} Sensor {sensor_id} published {size_kb}KB. RAM usage: {mem_diff_kb:.4f} KB")

        except requests.exceptions.RequestException as e:
            logger.error(f"Sensor {sensor_id} failed to send data to {target_url}: {e}")
        
        time.sleep(config.get("interval", 1.0))


if __name__ == "__main__":
    config_path = os.path.join(CONFIG_FILE_DIR, "line3.json") 
    try:
        ProductionLine(config_path).run()
    except Exception as e:
        logger.critical(f"Failed to run production line: {e}", exc_info=True)