"""
Control train with push buttons on Pins 2 and 3, while sensor data is recorded using MQTT.

Measured train speed as approximately 0.3 m/s or 300 mm/s.
"""

import json
from time import sleep_ms

import wifi
from detectors import AnalogueDetector, BehaviourEvent, EventOnChangeBehaviour, SchmittConverter
from hardware import flash_led, get_iso_datetime, set_rtc_time
from layout import AbsoluteDirection, Locomotive
from layout import AbsoluteDirection as facing
from machine import Pin
from umqtt.simple import MQTTClient

MQTT_BROKER = "192.168.88.108"

engine = Locomotive(motor_number=0, id="test_fast", orientation=facing.RIGHT)

button_right = Pin(12, Pin.IN, Pin.PULL_UP)
button_left = Pin(13, Pin.IN, Pin.PULL_UP)


def create_sensor(pin, trigger=200, release=250):
    return EventOnChangeBehaviour(
        SchmittConverter(
            AnalogueDetector(pin), trigger_threshold=trigger, release_threshold=release
        )
    )


class WheelCounter:
    """Handles sensor events and updates block counts based on direction of travel."""

    def __init__(self, name, sensor, left_block, right_block):
        self.name = name
        self.sensor = sensor
        self.left_block = left_block
        self.right_block = right_block
        self.last_event = BehaviourEvent.NONE

    def evaluate(self):
        self.last_event = self.sensor.check_event()
        return self.last_event

    def update_blocks(self, absolute_direction):
        """
        Update neighbouring block counts based on direction of travel.

        Left movement increases left block count and decreases right block count.

        Args:
            absolute_direction (AbsoluteDirection): Direction of travel.
        """
        if self.last_event == BehaviourEvent.NONE:
            return

        amount = 0.5
        if absolute_direction == AbsoluteDirection.RIGHT:
            amount *= -1
        if self.left_block:
            self.left_block.add_count(amount)
        if self.right_block:
            self.right_block.add_count(-amount)


class Block:
    """Block of track with a count of train cars."""

    def __init__(self, name):
        self.name = name
        self.count = 0

    def add_count(self, amount: float):
        """
        Increment count of passing train cars.

        An amount of 0.5 can indicate a car occupying two evaluators simultaneously.
        """
        self.count += amount
        if self.count < 0:
            print(f"WARNING: Evaluator {self.name} has a negative count of {self.count}")

        print(f"Evaluator {self.name} count: {self.count}")


# Software elements for handling how many wagons are in which block
blocks = {
    "0_SHED": Block("0_SHED"),
    "1_POINT": Block("1_POINT"),
    "2_THROUGH": Block("2_THROUGH"),
    "3_DIVERGE": Block("3_DIVERGE"),
}
# Hardware sensors
sensors = {
    "POINT_BASE": create_sensor(26),
    # "POINT_THROUGH": create_sensor(27),
    "POINT_DIVERGE": create_sensor(28),
}
# Software sensor handlers for car counting and event handling
mapping = {
    "POINT_BASE": ("0_SHED", "1_POINT"),
    # "POINT_THROUGH": ("1_POINT", "2_THROUGH"),
    "POINT_DIVERGE": ("1_POINT", "3_DIVERGE"),
}
wheel_counters = {
    name: WheelCounter(name, sensors[name], blocks[left_block], blocks[right_block])
    for name, (left_block, right_block) in mapping.items()
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
    for name, counter in wheel_counters.items():
        sensors[name].parent_behaviour.detector.read()
        counter.evaluate()  # reads the sensor and updates the event
        counter.update_blocks(engine.movement_direction())

    data = {
        "timestamp": get_iso_datetime(),
        "engine_velocity": engine.velocity * 10,  # for scaling against light sensors
    }
    data.update(
        {key.lower() + "_value": sensor.parent_behaviour.value() for key, sensor in sensors.items()}
    )
    data.update(
        {
            key.lower() + "_present": 350 if sensor.is_present() else 0
            for key, sensor in sensors.items()
        }
    )
    data.update({"block_" + key.lower(): block.count * 100 for key, block in blocks.items()})
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
