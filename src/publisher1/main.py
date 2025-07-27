import json
import os
import logging
import time
import requests
import psutil
import coloredlogs
from waitress import serve
from sensors.base_sensor import SensorConfig
from sensors import VibrationSensor, TemperatureSensor, QualitySensor, SecuritySensor

# UNIFIED AND COLORED LOGGING CONFIGURATION
LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
coloredlogs.install(level='INFO', fmt=LOG_FORMAT, isatty=True)
logger = logging.getLogger("Producer-1")

DROPPER_URL = os.getenv("DROPPER_URL", "http://dropper:5000/data")
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

    def send_data(self, sensor, config):
        mem_before_kb = self.process.memory_info().rss / 1024
        
        payload_str = sensor.generate_payload()
        
        # Log the generated payload size for visibility.
        size_kb = len(payload_str) // 1024
        sensor_id_for_log = "encrypted"
        if "encrypted_payload" not in payload_str:
            try:
                sensor_id_for_log = json.loads(payload_str).get("sensor_id", "N/A")
            except json.JSONDecodeError:
                sensor_id_for_log = "unknown"
        logger.info(f"Sensor {sensor_id_for_log} generated payload of {size_kb} KB.")
        
        payload_dict = json.loads(payload_str)
        
        try:
            response = requests.post(DROPPER_URL, json=payload_dict, timeout=10)
            response.raise_for_status()
            sensor_type_log = "secure" if "encrypted_payload" in payload_dict else payload_dict.get("type", "N/A")
            
            mem_after_kb = self.process.memory_info().rss / 1024
            mem_diff_kb = mem_after_kb - mem_before_kb
            logger.info(f"Sensor type '{sensor_type_log}' published data. RAM usage delta: {mem_diff_kb:.4f} KB")

        except requests.exceptions.RequestException as e:
            logger.error(f"Sensor failed to send data to {DROPPER_URL}: {e}")
        
        time.sleep(config.get("interval", 1.0))

if __name__ == "__main__":
    config_path = os.path.join(CONFIG_FILE_DIR, "line1.json") 
    try:
        ProductionLine(config_path).run()
    except Exception as e:
        logger.critical(f"Failed to run production line: {e}", exc_info=True)