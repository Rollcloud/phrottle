import json
import time

import network

WIFICONFIGFILE = "/.wifi/connections.json"


def connect(ssid, password, verbose=True):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        if verbose:
            print("waiting for connection...")
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError("network connection failed")
    else:
        if verbose:
            print("connected")
        status = wlan.ifconfig()
        address = status[0]
        if verbose:
            print("ip = " + address)

    return address


def connect_with_saved_credentials(verbose=True):
    """
    Read WIFI configuration from file system and connect to it
    For future compatibility we get a list of connections, though we only use the first one.
    """
    with open(WIFICONFIGFILE, "r", encoding="utf-8") as f:
        connections = json.load(f)

    ssid = connections[0]["ssid"]
    password = connections[0]["password"]
    return connect(ssid, password, verbose=verbose)
