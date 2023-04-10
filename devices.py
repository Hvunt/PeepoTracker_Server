
import os
import db
import asyncio, signal, uvloop
from gmqtt import Client

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

STOP = asyncio.Event()

def on_connect(client, flags, rc, properties):
  print("Connected with result code " + str(rc))
  client.subscribe("devices/+/data")

def on_message(client, topic, payload, qos, properties):
  # temp = f"devices/{client_id}/print"
  # if topic == temp:
  print(f"Received message '{payload}' on topic '{topic}'")

def on_disconnect(client, packet, exc=None):
  print("Disconnected")

def ask_exit(*args):
  STOP.set()

class DevicesMQTTHandler():

  def __init__(self, client_id, address, port, username='', password=''):
    self._client_id = client_id
    self.client = Client(self._client_id)
    self.client.set_auth_credentials(username, password)
    
    self.client.on_connect = on_connect
    self.client.on_message = on_message
    self.client.on_disconnect = on_disconnect

    self._address = address
    self._port = port
  
  async def send_data(self, device_id, message : str):
    if self.client.is_connected:
      self.client.publish(f"devices/{device_id}/print", message)
    else:
      print("MQTT Client doesn't connected")

  def connect(self):
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)
    loop.run_until_complete(self._main_thread())

  async def _main_thread(self):
    
    await self.client.connect(self._address, self._port)
    # await STOP.wait()
    # await self.client.disconnect()
    