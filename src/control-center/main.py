import paho.mqtt.client as mqtt
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ControlCenter")

class ControlCenter:
    def __init__(self):
        self.client = mqtt.Client(client_id="CONTROL-CENTER")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe("factory/#")
        logger.info("Connected to MQTT broker")
        
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload)
            size_kb = len(msg.payload) // 1024
            
            logger.info(f"Received {size_kb}KB from {msg.topic}")
            
            # Alert logic
            if payload.get('x', 0) > 8.0:
                logger.warning(f"High vibration detected! {payload['x']} mm/s")
                
            if payload.get('defect_count', 0) > 3:
                logger.error(f"Quality alert! {payload['defect_count']} defects")
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            
    def start(self):
        self.client.connect("10.0.5.2", 1883)
        self.client.loop_forever()

if __name__ == "__main__":
    center = ControlCenter()
    center.start()
