import json

import utime
import wifi
from detectors import (
    AGCConverter,
    AnalogueDetector,
    BehaviourEvent,
    DebounceBehaviour,
    DigitalDetector,
    EventOnChangeBehaviour,
    InverterBehaviour,
    SchmittConverter,
    SimpleThresholdConverter,
)
from umqtt.simple import MQTTClient

MQTT_BROKER = "192.168.88.117"

COUNT_THRESHOLD = 50
CLEAR_THRESHOLD = 60
FOUND_THRESHOLD = 20

MAX_SPEED = 500  # mm/s
MIN_WAGON_LENGTH = 25  # 1 inch in mm
REFLECTOR_LENGTH = 5  # mm

min_trigger_interval = int(MIN_WAGON_LENGTH / MAX_SPEED * 1000)  # 83 ms
min_trigger_duration = int(REFLECTOR_LENGTH / MAX_SPEED * 1000)  # 17 ms


def create_touch_sensor(gpio_number):
    """Create a debounced touch sensor."""
    touch_detector = DigitalDetector(gpio_number)
    touch_converter = SimpleThresholdConverter(touch_detector, threshold=1)
    touch_debouncer = DebounceBehaviour(touch_converter, debounce_time_ms=1000)
    return touch_debouncer


def create_end_of_track_sensor(gpio_number):
    """Create a debounced end-of-track sensor."""
    eot_detector = DigitalDetector(gpio_number)
    eot_converter = SimpleThresholdConverter(eot_detector, threshold=1)
    eot_inverter = InverterBehaviour(eot_converter)
    eot_debouncer = DebounceBehaviour(eot_inverter, debounce_time_ms=1000)
    return eot_debouncer


def create_wagon_sensors(gpio_number):
    """
    Create wagon sensors.

    Returns a tuple of the wagon presence sensor and the wagon counter for the given GPIO number.
    """
    # Pin sensor
    wagon_detector = AnalogueDetector(gpio_number)

    # Wagon presence sensor
    wagon_converter = AGCConverter(wagon_detector, base_threshold=COUNT_THRESHOLD, gain=0.05)
    wagon_debouncer = DebounceBehaviour(wagon_converter, debounce_time_ms=300)

    # Wagon counter
    wagon_counter = SchmittConverter(
        wagon_detector,
        trigger_threshold=COUNT_THRESHOLD,
        release_threshold=CLEAR_THRESHOLD,
    )
    wagon_count_debouncer = DebounceBehaviour(wagon_counter, debounce_time_ms=min_trigger_interval)
    wagon_count_events = EventOnChangeBehaviour(wagon_count_debouncer)

    return wagon_debouncer, wagon_count_events


def move_wagon(sensor_key: str, is_triggered: bool, is_moving_left: bool) -> None:
    """Move a wagon based on the sensor key and trigger state."""
    global blocks

    rules = {
        "EOT_C": (None, 0),
        "POINT_BASE_C": (0, 1),
        "POINT_THROUGH_C": (1, 2),
        "POINT_DIVERGE_C": (1, 3),
    }

    if is_triggered:
        block_number = rules[sensor_key][0 if is_moving_left else 1]
        blocks[block_number] += 1
    else:
        # is released
        block_number = rules[sensor_key][1 if is_moving_left else 0]
        blocks[block_number] -= 1


def display(sensors, blocks):
    """Show a small diagram of sensor states in the console."""
    hide_cursor = "\033[?25l"
    show_cursor = "\033[?25h"
    start_of_previous_line = "\033[F"
    red = "\033[91m"
    reset = "\033[0m"

    sensor_replacements = {
        "A": "EOT_P",
        "B": "POINT_BASE_P",
        "C": "POINT_THROUGH_P",
        "D": "POINT_DIVERGE_P",
    }

    # fmt: off
    track_diagram = (
        "            /C--2--\n"
        "  |A--0--B=1       \n"
        "            \D--3--\n"
    )
    # fmt: on

    block_replacements = [
        red + str(abs(block)) + reset if block < 0 else str(block) for block in blocks
    ]
    # replace digits with {digits} to avoid replacing the same number twice
    track_diagram_format = "".join(
        f"{{{char}}}" if char.isdigit() else char for char in track_diagram
    )

    track_diagram = track_diagram_format.format(*block_replacements)

    for key, sensor_key in sensor_replacements.items():
        track_diagram = track_diagram.replace(key, "!" if sensors[sensor_key].is_present() else ":")

    value_strings = "\n".join(
        [
            f"{key}: {sensor.value()}"
            for key, sensor in sensors.items()
            if key in ["POINT_BASE_P", "POINT_THROUGH_P", "POINT_DIVERGE_P"]
        ]
    )

    return "".join(
        [
            hide_cursor,
            track_diagram,
            value_strings,
            start_of_previous_line * 5,
            show_cursor,
        ]
    )


# Sensor assignments
# 21 - distance sensor, end of track
# 26 - reflective sensor, point base
# 27 - reflective sensor, point through
# 28 - reflective sensor, point diverge

sensors = {}
sensors["EOT_P"] = create_end_of_track_sensor(21)
sensors["POINT_BASE_P"], sensors["POINT_BASE_C"] = create_wagon_sensors(26)
sensors["POINT_THROUGH_P"], sensors["POINT_THROUGH_C"] = create_wagon_sensors(27)
sensors["POINT_DIVERGE_P"], sensors["POINT_DIVERGE_C"] = create_wagon_sensors(28)

blocks = [0, 0, 0, 0]

wifi.connect_with_saved_credentials()
qt = MQTTClient("phrottle", MQTT_BROKER, keepalive=60 * 60 * 3)
qt.connect()

try:
    while True:
        payload = {}

        # monitor wagon counters
        is_moving_left = True
        for key in sensors:
            if key.endswith("_C"):
                event = sensors[key].check_event()
                if event == BehaviourEvent.TRIGGER:
                    move_wagon(key, True, is_moving_left)
                elif event == BehaviourEvent.RELEASE:
                    move_wagon(key, False, is_moving_left)

                value = sensors[key].parent_behaviour.parent_behaviour.detector.value
                payload[key] = value

        qt.publish(b"paper_wifi/test/phrottle", json.dumps(payload))

        print(display(sensors, blocks), end="")
        utime.sleep(0.01)

finally:
    qt.disconnect()
