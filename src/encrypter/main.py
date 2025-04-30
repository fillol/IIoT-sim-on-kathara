import paho.mqtt.client as mqtt
import logging
import json
import base64
import os
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Encrypter")

MQTT_BROKER_HOST = "10.0.0.2"
MQTT_BROKER_PORT = 1883
CLIENT_ID = "ENCRYPTER-SERVICE"
SUBSCRIBE_TOPIC = "secure/#" # Subscribe to all secure sensor topics
PUBLISH_TOPIC_TEMPLATE = "factory/{line_id}/{sensor_id}" # Template for republishing

class EncrypterService:
    def __init__(self):
        self.client = mqtt.Client(client_id=CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self._connection_lost = False

    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to the MQTT broker."""
        if rc == 0:
            logger.info(f"Connected successfully to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            client.subscribe(SUBSCRIBE_TOPIC)#, qos=1)
            logger.info(f"Subscribed to topic: {SUBSCRIBE_TOPIC}")
            self._connection_lost = False
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from the MQTT broker."""
        logger.warning(f"Disconnected from MQTT broker with result code {rc}. Reconnecting...")
        self._connection_lost = True

    def on_message(self, client, userdata, msg):
        """Callback when a message is received on a subscribed topic."""
        logger.info(f"Message received on topic {msg.topic} of size {len(msg.payload)} bytes.")
        try:
            # 1. Decode the incoming payload
            payload_str = msg.payload.decode('utf-8')
            original_payload_dict = json.loads(payload_str)

            # 2. Extract necessary info for republishing BEFORE encrypting
            line_id = original_payload_dict.get("line_id")
            sensor_id = original_payload_dict.get("sensor_id")

            if not line_id or not sensor_id:
                logger.warning(f"Missing 'line_id' or 'sensor_id' in message from {msg.topic}. Skipping.")
                return

            # 3. Encode the original payload string (not the dict) to Base64
            original_payload_bytes = payload_str.encode('utf-8')
            encoded_payload_bytes = base64.b64encode(original_payload_bytes)
            encoded_payload_str = encoded_payload_bytes.decode('utf-8')  # Convert Base64 bytes to string
            logger.info(f"Message from topic {msg.topic} successfully encrypted.")

            # 4. Create the new payload structure for republishing
            republish_payload = {
                "encrypted_payload": encoded_payload_str,
                "source": "secure",
            }
            republish_payload_str = json.dumps(republish_payload)
            republish_payload_bytes = republish_payload_str.encode('utf-8')

            # 5. Determine the target topic for republishing
            target_topic = PUBLISH_TOPIC_TEMPLATE.format(line_id=line_id, sensor_id=sensor_id)

            # 6. Republish the encrypted message to the standard topic
            client.publish(target_topic, payload=republish_payload_bytes, qos=1)
            logger.info(f"Encrypted message published to topic {target_topic}.")
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from message on topic {msg.topic}. Payload: {msg.payload[:100]}...")
        except UnicodeDecodeError:
            logger.error(f"Failed to decode payload as UTF-8 from topic {msg.topic}. Payload: {msg.payload[:100]}...")
        except Exception as e:
            logger.error(f"Error processing message from topic {msg.topic}: {e}", exc_info=True)

    def start(self):
        """Connects to the broker and starts the processing loop."""
        while True:
            try:
                logger.info(f"Attempting to connect to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
                self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
                self.client.loop_forever()
            except ConnectionRefusedError:
                logger.error(f"Connection refused by broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}. Retrying in 10 seconds...")
            except OSError as e:
                 logger.error(f"Network error connecting to broker: {e}. Retrying in 10 seconds...")
            except KeyboardInterrupt:
                 logger.info("Encrypter service stopped by user.")
                 self.client.disconnect()
                 break
            except Exception as e:
                 logger.error(f"An unexpected error occurred in the main loop: {e}. Retrying in 10 seconds...", exc_info=True)

            if not self._connection_lost:
                 time.sleep(10)


if __name__ == "__main__":
    service = EncrypterService()
    service.start()
