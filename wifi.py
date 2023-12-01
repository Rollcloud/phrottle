import json

from phew import connect_to_wifi
from phew.logging import LOG_ALL, disable_logging_types

WIFICONFIGFILE = "/.wifi/connections.json"

disable_logging_types(LOG_ALL)


def connect():
    """
    Read WIFI configuration from file system and connect to it
    For future compatibility we get a list of connections, though we only use the first one.
    """
    with open(WIFICONFIGFILE, "r", encoding="utf-8") as f:
        connections = json.load(f)

    print("Connecting to WiFi...")
    address = connect_to_wifi(connections[0]["ssid"], connections[0]["password"])
    print(f"Connected on {address}")
