import asyncio
import json
import os
import logging
from asyncio_mqtt import Client as MqttClient
from sensors.base_sensor import SensorConfig
from sensors import VibrationSensor, TemperatureSensor, QualitySensor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Publisher")

class ProductionLine:
    def __init__(self, config_file):
        with open(f"{config_file}") as f:
            self.config = json.load(f)
        self.sensors = self._init_sensors()

    def _init_sensors(self):
        sensors = []
        for cfg in self.config["sensors"]:
            sensor_class = {
                "vibration": VibrationSensor,
                "temperature": TemperatureSensor,
                "quality": QualitySensor
            }[cfg["type"]]

            sensors.append((
                sensor_class(
                    self.config["line_id"],
                    SensorConfig(
                        sensor_type=cfg["type"],
                        update_interval=cfg["interval"],
                        payload_variation=cfg["payload"],
                        qos=cfg["qos"]
                    )
                ),
                cfg
            ))
        return sensors

    async def run(self):
        # Inizializza il client MQTT DENTRO il contesto asincrono
        async with MqttClient(
            hostname="10.0.5.2",
            client_id=self.config["line_id"]
        ) as client:
            tasks = []
            for sensor, cfg in self.sensors:
                tasks.append(self._publish_sensor(client, sensor, cfg))
            await asyncio.gather(*tasks)

    async def _publish_sensor(self, client, sensor, config):
        while True:
            payload = await sensor.generate_payload()
            await client.publish(
                topic=f"factory/{sensor.line_id}/{sensor.sensor_id}",
                payload=payload,
                qos=config["qos"]
            )
            logger.info(f"Published {len(payload)//1024}KB to {sensor.line_id}")
            await asyncio.sleep(config["interval"])

if __name__ == "__main__":
    line = ProductionLine("line3.json")
    asyncio.run(line.run())
