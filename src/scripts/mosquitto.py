import json
import time

import hardware  # type: ignore
import wifi  # type: ignore
from umqtt.simple import MQTTClient

flash_led = hardware.flash_led

MQTT_BROKER = "192.168.88.108"

address = wifi.connect_with_saved_credentials()

flash_led(n=2)  # show that wifi connection was successful

qt = MQTTClient("pico", MQTT_BROKER, keepalive=300)
qt.connect()

try:
    while True:
        payload = {"temperature": hardware.get_internal_temperature()}
        qt.publish(b"paper_wifi/test/pico", json.dumps(payload))

        flash_led(n=1)
        time.sleep(5)
finally:
    qt.disconnect()
