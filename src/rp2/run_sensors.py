"""
Control train with push buttons on Pins 2 and 3, while sensor data is recorded using MQTT.

Measured train speed as approximately 0.3 m/s or 300 mm/s.
"""

import json
from time import sleep_ms

import wifi
from detectors import AnalogueDetector, SchmittConverter
from hardware import flash_led, get_iso_datetime, set_rtc_time
from layout import AbsoluteDirection as facing
from layout import Locomotive
from machine import Pin
from umqtt.simple import MQTTClient

MQTT_BROKER = "192.168.88.108"

engine = Locomotive(motor_number=0, id="test_fast", orientation=facing.RIGHT)

button_right = Pin(12, Pin.IN, Pin.PULL_UP)
button_left = Pin(13, Pin.IN, Pin.PULL_UP)


def create_sensor(pin, trigger=100, release=250):
    return SchmittConverter(
        AnalogueDetector(pin), trigger_threshold=trigger, release_threshold=release
    )


sensors = {
    "POINT_BASE": create_sensor(26),
    "POINT_THROUGH": create_sensor(27),
    "POINT_DIVERGE": create_sensor(28),
}


def control_train(acceleration=100):
    left_pressed = not button_left.value()
    right_pressed = not button_right.value()

    if left_pressed and right_pressed:
        engine.engine.brake(acceleration)
    elif left_pressed:
        engine.accelerate(-acceleration)
    elif right_pressed:
        engine.accelerate(acceleration)
    else:
        engine.brake(acceleration)


def read_sensors():
    for sensor in sensors.values():
        sensor.detector.read()
    data = {
        "timestamp": get_iso_datetime(),
        "engine_velocity": engine.velocity * 10,  # for scaling against light sensors
    }
    data.update({key.lower() + "_value": sensor.value() for key, sensor in sensors.items()})
    data.update(
        {
            key.lower() + "_present": 350 if sensor.is_present() else 0
            for key, sensor in sensors.items()
        }
    )
    return data


def send_sensor_data(sensor_data):
    payload = sensor_data
    qt.publish(b"paper_wifi/test/phrottle", json.dumps(payload))
    print(json.dumps(sensor_data), end="\r")


def main_loop():
    # print("Running main loop")
    control_train()
    # print("Engine velocity:", engine.velocity)
    sensor_data = read_sensors()
    send_sensor_data(sensor_data)
    sleep_ms(1)


if __name__ == "__main__":
    try:
        address = wifi.connect_with_saved_credentials()
        flash_led(n=2)  # show that wifi connection was successful
        set_rtc_time()
        print("Time set")
        qt = MQTTClient("pico", MQTT_BROKER, keepalive=300)
        qt.connect()
        print("Connected to MQTT")
        print("Running main")
        while True:
            main_loop()
    except KeyboardInterrupt:
        print("Keyboard exit detected")
    finally:
        engine.stop()
        qt.disconnect()
