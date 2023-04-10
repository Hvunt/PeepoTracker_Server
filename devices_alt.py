import asyncio
import logging
import paho.mqtt.client as mqtt

class AsyncMQTTClient:
    def __init__(self, broker_host, broker_port=1883, client_id="", username="", password=""):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.connected = False
        self.logger = logging.getLogger(__name__)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.logger.info("Connected to MQTT broker")
        else:
            self.logger.error(f"Failed to connect to MQTT broker, error code: {rc}")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        # asyncio.create_task(self._handle_message(topic, payload))
        # await self._handle_message(topic, payload)

    async def _handle_message(self, topic, payload):
        pass

    def connect(self):
        self.client.username_pw_set(self.username, self.password)
        self.client.connect(self.broker_host, self.broker_port)
        self.logger.info("Connecting to MQTT broker")

    def subscribe(self, topic, callback):
        self.client.subscribe(topic)
        self.logger.info(f"Subscribed to topic: {topic}")
        self._handle_message = callback

    async def send_data(self, device_id, data):
        res = False
        if device_id != 0:
            if not self.connected:
                self.logger.error("Cannot send data - not connected to MQTT broker")
            else:
                topic = f"devices/{device_id}/print"
                payload = str(data)
                self.client.publish(topic, payload)
                self.logger.info(f"Sent data to topic: {topic}")
                res = True
        return res

    async def start(self):
        self.client.loop_start()
        while not self.connected:
            await asyncio.sleep(0.1)
        self.logger.info("MQTT client started")

    async def stop(self):
        self.client.loop_stop()
        self.logger.info("MQTT client stopped")