import paho.mqtt.client as mqtt
import logging
import json
import base64
import os
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ControlCenter")

# --- Configuration ---
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "10.0.0.2")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
CLIENT_ID = "CONTROL-CENTER"
SUBSCRIBE_TOPIC = "factory/#" # Sottoscrivi a tutti i topic factory

class ControlCenter:
    def __init__(self):
        self.client = mqtt.Client(client_id=CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self._connection_lost = False


    def on_connect(self, client, userdata, flags, rc):
        """Callback alla connessione al broker MQTT."""
        if rc == 0:
            logger.info(f"Connesso con successo al broker MQTT a {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            # Sottoscrivi alla gerarchia principale dei topic factory
            client.subscribe(SUBSCRIBE_TOPIC)#, qos=1)
            logger.info(f"Sottoscritto al topic: {SUBSCRIBE_TOPIC}")
            self._connection_lost = False
        else:
            logger.error(f"Connessione al broker MQTT fallita, return code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback alla disconnessione dal broker MQTT."""
        logger.warning(f"Disconnesso dal broker MQTT con codice {rc}. Riconnessione...")
        self._connection_lost = True

    def on_message(self, client, userdata, msg):
        """Callback alla ricezione di un messaggio."""
        try:
            # Prova a decodificare il payload come JSON
            payload_str = msg.payload.decode('utf-8')
            payload_dict = json.loads(payload_str)
            size_kb = len(msg.payload) // 1024

            # Controlla se è un messaggio criptato dal servizio encrypter
            if payload_dict.get("source") == "secure" and "encrypted_payload" in payload_dict:
                logger.info(f"Received SECURE message ({size_kb}KB) originally from sensor {msg.topic.split('/')[-1]} (via Encrypter)")

                try:
                    encrypted_data = payload_dict["encrypted_payload"]
                    decoded_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
                    decrypted_payload_str = decoded_bytes.decode('utf-8')
                    decrypted_data = json.loads(decrypted_payload_str)

                    status_code = decrypted_data.get("status_code")
                    access_attempts = decrypted_data.get("access_attempts", 0)
                    criticality = decrypted_data.get("criticality", "Unknown")
                    source_ip = decrypted_data.get("source_ip", "N/A")

                    # Logica di alert specifica per i dati di sicurezza
                    if status_code in [401, 403]:
                        logger.warning(f"[Encrypted] Access issue detected! Status: {status_code}, IP: {source_ip}, Attempts: {access_attempts}")
                    elif status_code == 500:
                        logger.warning(f"[Encrypted] Internal error reported! Status: {status_code}, IP: {source_ip}")
                    elif criticality == "High":
                        logger.warning(f"[Encrypted] High criticality event! Status: {status_code}, IP: {source_ip}, Attempts: {access_attempts}")
                    else:
                        logger.info(f"[Encrypted] Security status OK (Code: {status_code})") # Log opzionale per eventi normali

                except (base64.binascii.Error, UnicodeDecodeError) as e:
                    logger.error(f"Failed to decode Base64 secure payload from {msg.topic}: {e}")
                except json.JSONDecodeError:
                     logger.error(f"Failed to parse decrypted JSON data from secure message on topic {msg.topic}")
                except Exception as e:
                     logger.error(f"Error processing decrypted secure payload from {msg.topic}: {e}", exc_info=True)

                return

            logger.info(f"Received standard message ({size_kb}KB) from {msg.topic}")
            sensor_type = payload_dict.get("type")

            if sensor_type == "vibration":
                vibration_x = payload_dict.get('x', 0)
                if isinstance(vibration_x, (int, float)) and vibration_x > 8.0:
                    logger.warning(f"High vibration detected on {msg.topic}! Value: {vibration_x:.2f} mm/s")

            elif sensor_type == "quality":
                 defect_count = payload_dict.get('defect_count', 0)
                 if isinstance(defect_count, int) and defect_count > 3:
                    logger.error(f"Quality alert on {msg.topic}! {defect_count} defects detected.")

            elif sensor_type == "temperature":
                 temp_c = payload_dict.get('temperature', 0)
                 if isinstance(temp_c, (int, float)) and temp_c > 50.0: # Soglia di esempio
                     logger.warning(f"High temperature detected on {msg.topic}! Value: {temp_c:.1f}°C")

        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message on topic {msg.topic}. Payload (first 100 bytes): {msg.payload[:100]}...")
        except UnicodeDecodeError:
            logger.error(f"Failed to decode payload as UTF-8 from topic {msg.topic}. Payload (first 100 bytes): {msg.payload[:100]}...")
        except Exception as e:
            logger.error(f"Error processing message from topic {msg.topic}: {e}", exc_info=True)

    def start(self):
        """Si connette al broker e avvia il loop di elaborazione."""
        while True:
            try:
                logger.info(f"Tentativo di connessione al broker MQTT a {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
                self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
                self.client.loop_forever()
            except ConnectionRefusedError:
                logger.error(f"Connessione rifiutata dal broker a {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}. Riprovo tra 10 secondi...")
            except OSError as e:
                 logger.error(f"Errore di rete durante la connessione al broker: {e}. Riprovo tra 10 secondi...")
            except KeyboardInterrupt:
                 logger.info("Control Center fermato dall'utente.")
                 self.client.disconnect()
                 break
            except Exception as e:
                 logger.error(f"Errore inaspettato nel loop principale: {e}. Riprovo tra 10 secondi...", exc_info=True)

            if not self._connection_lost:
                 time.sleep(10)


if __name__ == "__main__":
    center = ControlCenter()
    center.start()
