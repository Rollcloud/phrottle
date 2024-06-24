# boot.py -- run on boot-up
import json

from machine import Pin
from phew import connect_to_wifi
from phew.logging import LOG_ALL, disable_logging_types

from lib import morse

disable_logging_types(LOG_ALL)

# Pin mappings
led = Pin("LED", Pin.OUT)

# read WIFI configuration from file system and connect to it
# for future compatibility we get a list of connections, though we only use the first one.
wifiConfigFile = "/.wifi/connections.json"
with open(wifiConfigFile, "r", encoding="utf-8") as f:
    connections = json.load(f)

addr = connect_to_wifi(connections[0]["ssid"], connections[0]["password"])
print(addr)

# send last three digits of IP address in morse code
morse.send(addr[-3:], wpm=10)
