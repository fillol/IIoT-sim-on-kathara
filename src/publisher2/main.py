import json
import os
import logging
import time
import requests
import psutil
import multiprocessing
import math
import random
from sensors.base_sensor import SensorConfig
from sensors import VibrationSensor, TemperatureSensor, QualitySensor, SecuritySensor

LOG_FORMAT = '%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("Producer")

CONTROL_CENTER_URL = os.getenv("CC_URL", "http://10.3.4.2:5000/data")
ENCRYPTER_URL = os.getenv("ENCRYPTER_URL", "http://10.2.1.2:5000/encrypt")
CONFIG_FILE_DIR = os.getenv("CONFIG_FILE_DIR", ".")


def digital_twin_worker(shared_value, stop_event):
    """
    Simulates a digital twin model running in the background.
    Its computational and memory load is intentionally variable.
    """
    logger.info("Digital Twin worker process started.")
    worker_process = psutil.Process(os.getpid())
    
    while not stop_event.is_set():
        # Make the load variable to simulate real-world fluctuations.
        # It will sometimes do a heavy calculation, sometimes a light one.
        if random.random() > 0.7:
            # Simulate a "heavy" analysis cycle
            loop_count = 20000
            # Also allocate a variable-sized memory block
            dummy_block = bytearray(random.randint(1024 * 10, 1024 * 50)) # 10-50 KB
        else:
            # Simulate a "light" baseline cycle
            loop_count = 1000
            dummy_block = bytearray(random.randint(1024 * 1, 1024 * 5)) # 1-5 KB
        
        result = 0
        for i in range(loop_count):
            result += math.sqrt(random.random() * i)
        
        # Write the result to shared memory for the main process
        with shared_value.get_lock():
            shared_value.value = result
        
        # The memory allocated by dummy_block is released here, creating RAM fluctuations.
        del dummy_block
        time.sleep(random.uniform(0.5, 1.5))
    
    logger.info("Digital Twin worker process stopped.")


class ProductionLine:
    def __init__(self, config_file_path):
        with open(config_file_path) as f:
            self.config = json.load(f)
        self.sensors = self._init_sensors()
        self.main_process = psutil.Process(os.getpid())
        
        # I'm using a background process to simulate the constant load
        # of a Digital Twin model. This is more realistic than a dummy calc.
        self.dt_shared_value = multiprocessing.Value('d', 0.0)
        self.stop_event = multiprocessing.Event()
        
        self.worker_process = multiprocessing.Process(
            target=digital_twin_worker,
            args=(self.dt_shared_value, self.stop_event)
        )
        self.worker_process.daemon = True
        self.worker_process.start()

    def _init_sensors(self):
        sensors = []
        smap = {"vibration": VibrationSensor, "temperature": TemperatureSensor, "quality": QualitySensor, "security": SecuritySensor}
        for cfg in self.config.get("sensors", []):
            s_class = smap.get(cfg.get("type"))
            if s_class:
                sensors.append((s_class(self.config["line_id"], SensorConfig(cfg["type"], float(cfg["interval"]), cfg["payload"], int(cfg.get("qos",1)))), cfg))
        return sensors

    def run(self):
        try:
            logger.info(f"Starting REST producer for line {self.config.get('line_id', 'N/A')}")
            while True:
                for sensor, config in self.sensors:
                    self.send_data(sensor, config)
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received.")
        finally:
            logger.info("Stopping Digital Twin worker...")
            self.stop_event.set()
            self.worker_process.join(timeout=5)
            logger.info("Producer shutdown complete.")

    def send_data(self, sensor, config):
        payload_str = sensor.generate_payload()
        payload_dict = json.loads(payload_str)
        
        # The sensor payload now includes a live value from the DT worker
        with self.dt_shared_value.get_lock():
            payload_dict['dt_anomaly_score'] = self.dt_shared_value.value
            
        payload_str_final = json.dumps(payload_dict)
        size_kb = len(payload_str_final) // 1024
        sensor_id = payload_dict.get("sensor_id", "N/A")

        is_secure = sensor.config.sensor_type == "security"
        target_url = ENCRYPTER_URL if is_secure else CONTROL_CENTER_URL
        log_prefix = "[SECURE]" if is_secure else "[STANDARD]"
        
        # Log the total process memory, which includes the DT worker's impact.
        # This is a more realistic way to monitor the service's footprint.
        total_ram_kb = self.main_process.memory_info().rss / 1024
        logger.info(f"{log_prefix} Sensor {sensor_id} sending {size_kb}KB. Total process RAM: {total_ram_kb:.2f} KB")
        
        try:
            response = requests.post(target_url, json=payload_dict, timeout=10)
            response.raise_for_status()
            # No need for a "delivered" message, it just clutters the log
        except requests.exceptions.RequestException as e:
            logger.error(f"Sensor {sensor_id} failed to send data to {target_url}: {e}")
        
        time.sleep(config.get("interval", 1.0))


if __name__ == "__main__":
    # Change this line for publisher 2 and 3
    config_path = os.path.join(CONFIG_FILE_DIR, "line1.json") 
    try:
        ProductionLine(config_path).run()
    except Exception as e:
        logger.critical(f"Failed to run production line: {e}", exc_info=True)