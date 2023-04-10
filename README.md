# GPS-tracker project. Server side

The server is used to handle requests from the telegram bot to designated ESP32-based GPS-trackers.

All the device IDs are unique. Pairs [Telegram user ID]:[device ID] are stored in a SQLite database.

Base version of the Telegram bot had following commands:
- /add_device - add a device with a given ID. Also we can assign a Tag to the ID. Example: /add_device 1234567890 Car
- /delete_device - delete a device with a given ID or Tag. Example: /delete_device 1234567890
- /get_devices - get the list of all assigned to this Telegram account devices.
- /get_location - get location with a given ID or Tag. If you want to get live updates of the location (updated every 10 seconds), so you need to provide an update time value in minutes. Without this parameter, you will get just the current position of a device. Example: /get_location Car 1
- /send_message - print a message on a device screen with a given ID or TAG. Max 100 symbols. Example: /send_message Car test message

MQTT is used as a connection protocol between the devices and the server. Mosquitto is used as the broker. 