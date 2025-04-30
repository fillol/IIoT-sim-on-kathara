import asyncio
import json
import os
import logging
from asyncio_mqtt import Client as MqttClient
from sensors.base_sensor import SensorConfig
from sensors import VibrationSensor, TemperatureSensor, QualitySensor, SecuritySensor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Producer")

MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "10.0.0.2")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
CONFIG_FILE_DIR = os.getenv("CONFIG_FILE_DIR", ".")

class ProductionLine:
    def __init__(self, config_file_path):
        """
        Initializes the production line simulator.
        Args:
            config_file_path (str): Path to the JSON configuration file.
        """
        try:
            with open(config_file_path) as f:
                self.config = json.load(f)
            logger.info(f"Loaded configuration from {config_file_path}")
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_file_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {config_file_path}")
            raise
        self.sensors = self._init_sensors()

    def _init_sensors(self):
        """Initializes sensor objects based on the configuration."""
        sensors = []
        # Map sensor type strings to their respective classes
        sensor_class_map = {
            "vibration": VibrationSensor,
            "temperature": TemperatureSensor,
            "quality": QualitySensor,
            "security": SecuritySensor # Add the new sensor type
        }

        if "sensors" not in self.config or not isinstance(self.config["sensors"], list):
             logger.error("Invalid or missing 'sensors' array in configuration.")
             return []

        for i, cfg in enumerate(self.config["sensors"]):
            sensor_type = cfg.get("type")
            if not sensor_type:
                logger.warning(f"Sensor config at index {i} missing 'type'. Skipping.")
                continue

            sensor_class = sensor_class_map.get(sensor_type)
            if not sensor_class:
                logger.warning(f"Unknown sensor type '{sensor_type}' at index {i}. Skipping.")
                continue

            try:
                # Validate required config fields
                interval = float(cfg["interval"])
                payload_variation = cfg["payload"]
                qos = int(cfg["qos"])

                sensor_instance = sensor_class(
                    self.config["line_id"],
                    SensorConfig(
                        sensor_type=sensor_type,
                        update_interval=interval,
                        payload_variation=payload_variation,
                        qos=qos
                    )
                )
                sensors.append((sensor_instance, cfg))
                logger.info(f"Initialized {sensor_type} sensor (ID: {sensor_instance.sensor_id})")
            except KeyError as e:
                logger.warning(f"Missing key {e} in sensor config at index {i} ({sensor_type}). Skipping.")
            except (ValueError, TypeError) as e:
                 logger.warning(f"Invalid value type in sensor config at index {i} ({sensor_type}): {e}. Skipping.")

        return sensors

    async def run(self):
        """Connects to MQTT and starts publishing sensor data."""
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT} with Client ID {self.config['line_id']}")
        try:
            # Initialize MQTT client within the async context
            async with MqttClient(
                hostname=MQTT_BROKER_HOST,
                port=MQTT_BROKER_PORT,
                client_id=self.config["line_id"]
            ) as client:
                logger.info("Successfully connected to MQTT broker.")
                tasks = []
                for sensor, cfg in self.sensors:
                    # Pass the client instance to the publishing task
                    tasks.append(self._publish_sensor(client, sensor, cfg))
                if tasks:
                    await asyncio.gather(*tasks)
                else:
                    logger.warning("No sensors initialized, nothing to publish.")
        except ConnectionRefusedError:
             logger.error(f"MQTT Connection refused. Is the broker running at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}?")
        except Exception as e:
             logger.error(f"An unexpected error occurred during MQTT connection or publishing: {e}", exc_info=True)


    async def _publish_sensor(self, client, sensor, config):
        """Generates and publishes data for a single sensor periodically."""
        interval = config.get("interval", 1.0) # Default interval if missing
        qos = config.get("qos", 0) # Default QoS if missing

        if isinstance(sensor, SecuritySensor):
            topic = f"secure/{sensor.line_id}"
            log_prefix = "[SECURE] "
        else:
            # Use the standard topic for other sensors
            topic = f"factory/{sensor.line_id}/{sensor.sensor_id}"
            log_prefix = ""

        logger.info(f"{log_prefix}Starting publisher loop for sensor {sensor.sensor_id} on topic {topic} with interval {interval}s")

        while True:
            try:
                payload_str = await sensor.generate_payload()
                payload_bytes = payload_str.encode('utf-8') # Encode string to bytes for publishing

                await client.publish(
                    topic=topic,
                    payload=payload_bytes,
                    qos=qos
                )
                logger.info(f"{log_prefix}Published {len(payload_bytes)//1024}KB to {topic} (Sensor: {sensor.sensor_id})")
                await asyncio.sleep(interval)
            except asyncio_mqtt.MqttError as e:
                 logger.error(f"MQTT Error for sensor {sensor.sensor_id} on topic {topic}: {e}. Attempting to reconnect implicitly...")
                 await asyncio.sleep(5) # Wait before retrying
            except Exception as e:
                 logger.error(f"Error in publishing loop for sensor {sensor.sensor_id}: {e}", exc_info=True)
                 await asyncio.sleep(interval) # Wait before retrying

if __name__ == "__main__":
    config_path = os.path.join(CONFIG_FILE_DIR, "line1.json")
    try:
        line = ProductionLine(config_path)
        asyncio.run(line.run())
    except FileNotFoundError:
        logger.critical(f"Cannot start producer: Configuration file '{config_path}' not found.")
    except Exception as e:
        logger.critical(f"Failed to initialize or run the production line: {e}", exc_info=True)
