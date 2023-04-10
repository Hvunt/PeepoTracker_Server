#!/usr/bin/env python3
import time
from telebot.async_telebot import AsyncTeleBot
import telebot
import db, devices_alt
import asyncio

from dotenv import dotenv_values
config = dotenv_values("opt.env")
token = config['TELEGRAM_BOT_TOKEN']

DEFAULT_LIVE_PERIOD = 60

# used to send a test location
test_lon = 28.85912092275951
test_lat = 47.012660784376365
test_step = 0.0001

mqtt_client_id = config['MQTT_OWN_ID']
mqtt_server_username = config['MQTT_SERVER_LOGIN']
mqtt_server_password = config['MQTT_SERVER_PASS']
mqtt_broker_address = config['MQTT_BROKER_ADDRESS']
mqtt_broker_port = config['MQTT_BROKER_PORT']

test_device_id = config['TEST_DEVICE_ID']

bot = AsyncTeleBot(token)
devicesHandler = devices_alt.AsyncMQTTClient(
  broker_host=mqtt_broker_address, 
  broker_port=int(mqtt_broker_port), 
  username=mqtt_server_username, 
  password=mqtt_server_password, 
  client_id=mqtt_client_id
)

async def mqtt_messages_handler(topic, payload):
  print(f"Received MQTT message: {topic} - {payload}")


async def send_data(client, device_id, payload):
  await devicesHandler.send_data(device_id, payload)


@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
  answer = "Use the list of commands"
  await bot.reply_to(message, answer)


@bot.message_handler(commands=['add_device'])
async def add_new_device_handler(message):
  args = message.text.split()
  user_id = message.from_user.id
  if len(args) > 1:
    tag = ""
    if len(args) > 2:
      tag = args[2]
    res = db.append_device(int(user_id), int(args[1]), tag)
    if res:
      await bot.reply_to(message, "Device has been added")
    else:
      await bot.reply_to(message, "Device already exist")
  else:
    await bot.reply_to(message, "Device ID can't be empty")


@bot.message_handler(commands=['send_message'])
async def send_message_handler(message):
  answer = "Please, provide more information. For using this command send /send_message [deviceID or TAG] [message]"

  args = message.text.split()
  payload = message.text[message.text.find(' ', 14)+1 :]
  user_id = message.from_user.id
  device_id = 0
  tag = ""
  if len(args) > 2:
    if((str(args[1]) == 'test')):
      await devicesHandler.send_data(test_device_id, payload)
      answer = "Message has been sent"
    else:

      if args[1].isnumeric():
        device_id = args[1]
      else:
        tag = args[1]

      if db.is_exist(user_id, device_id, tag):
        device_id = db.get_device_by_tag(user_id, tag)
        await devicesHandler.send_data(device_id, payload)
        answer = "Message has been sent"
      else:
        answer = f"Sorry, you don't have connected devices with a provided ID/Tag {args[1]}. To get the list of all connected devices use the /get_devices command"

  await bot.reply_to(message, answer)


@bot.message_handler(commands=['get_devices'])
async def get_devices_handler(message):
  answer = ""
  user_id = message.from_user.id
  devices = db.get_devices(int(user_id))
  if len(devices) > 0:
    for row in devices:
      answer += f"{row[2]} {row[0]}\n"
  else:
    answer = "Sorry, you don't have any connected devices :("

  await bot.reply_to(message, answer)


@bot.message_handler(commands=['delete_device'])
async def delete_device(message):
  device = message.text.split()
  if len(device) > 1:
    if device[1].isnumeric():
      db.delete_device_by_ID(device[1])
    else:
      db.delete_device_by_TAG(device[1])
    await bot.reply_to(message, f"The device {device[1]} has been removed")
  else:
    await bot.reply_to(message, "The device ID can't be empty")


@bot.message_handler(func=lambda message: message.text[0] != '/')
async def handle_buttons(message):
  remove_keyboard = telebot.types.ReplyKeyboardRemove()
  await bot.reply_to(message,
               f"Coordinates of the device:{message.text}",
               reply_markup=remove_keyboard)
  await bot.send_location(message.from_user.id, test_lat, test_lon)


async def update_location(chat_id, message_id, live_period):
  for i in range(1, int(live_period / 10) - 1):
    time.sleep(10)
    await bot.edit_message_live_location(test_lat + i * test_step,
                                   test_lon + i * test_step,
                                   chat_id=chat_id,
                                   message_id=message_id)


@bot.message_handler(commands=['get_location'])
async def get_location(message):
  user_id = message.from_user.id
  args = message.text.split()
  if (len(args) > 1):
    chat_id = message.chat.id
    live_period = DEFAULT_LIVE_PERIOD
    tag = ""
    device_id = 0
    if args[1].isnumeric():
      device_id = int(args[1])
    else:
      tag = args[1]

    if db.is_exist(user_id, device_id, tag):
      await bot.reply_to(message, f"Coordinates of the device:{device_id} {tag}")

      if (len(args) > 2):
        live_period = args[2]
      answer = await bot.send_location(chat_id,
                                 test_lat,
                                 test_lon,
                                 live_period=live_period)
      await update_location(chat_id, answer.id, live_period)
    else:
      await bot.reply_to(message, "Sorry, I don't know the device :(")
  else:
    devices = db.get_devices(int(user_id))
    if len(devices) > 0:
      keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
      for device in devices:
        keyboard.add(f"{device[0]} {device[2]}")
      await bot.send_message(user_id, "Choose a device: ", reply_markup=keyboard)
    else:
      await bot.reply_to(
        message,
        "Which device to track? You can use ID or Tag. To get the list of all connected devices use the /get_devices command"
      )

devicesHandler.connect()
devicesHandler.subscribe("devices/+/data", mqtt_messages_handler)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.create_task(devicesHandler.start())
loop.create_task(bot.polling(non_stop=True))
loop.run_forever()