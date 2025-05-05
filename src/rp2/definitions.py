"""
Define layout elements and sensor configurations.

```py
from definitions import loco, point, sensors
```
"""

import json

from detectors import (
    AGCConverter,
    AnalogueDetector,  # type: ignore
    DebounceBehaviour,
    DigitalDetector,
    EventOnChangeBehaviour,
    InverterBehaviour,
    SchmittConverter,
    SimpleThresholdConverter,
)
from layout import AbsoluteDirection as Facing  # type: ignore
from layout import Locomotive, Point  # type: ignore

FOUND_THRESHOLD = 20

MAX_SPEED = 500  # mm/s
MIN_WAGON_LENGTH = 25  # 1 inch in mm
REFLECTOR_LENGTH = 5 / 2  # mm

min_trigger_interval = int(MIN_WAGON_LENGTH / MAX_SPEED * 1000)  # 83 ms
min_trigger_duration = int(REFLECTOR_LENGTH / MAX_SPEED * 1000)  # 17 ms

# load config from config.json
with open("config.json", "r") as f:
    config = json.load(f)


point = Point(motor_number=1, id="Point")
loco = Locomotive(motor_number=0, id="test", orientation=Facing.LEFT)


def create_touch_sensor(gpio_number):
    """Create a debounced touch sensor."""
    touch_detector = DigitalDetector(gpio_number)
    touch_converter = SimpleThresholdConverter(touch_detector, threshold=1)
    touch_debouncer = DebounceBehaviour(touch_converter, debounce_time_ms=1000)
    touch_events = EventOnChangeBehaviour(touch_debouncer)
    return touch_events


def create_end_of_track_sensor(gpio_number):
    """Create a debounced end-of-track sensor."""
    eot_detector = DigitalDetector(gpio_number)
    eot_converter = SimpleThresholdConverter(eot_detector, threshold=1)
    eot_inverter = InverterBehaviour(eot_converter)
    eot_debouncer = DebounceBehaviour(eot_inverter, debounce_time_ms=1000)
    eot_events = EventOnChangeBehaviour(eot_debouncer)
    return eot_events


def create_wagon_sensors(gpio_number):
    """
    Create wagon sensors.

    Returns a tuple of the wagon presence sensor and the wagon counter for the given GPIO number.
    """
    # Pin sensor
    wagon_detector = AnalogueDetector(gpio_number)

    # Wagon presence sensor
    wagon_converter = AGCConverter(wagon_detector, base_threshold=FOUND_THRESHOLD, gain=0.05)
    wagon_debouncer = DebounceBehaviour(wagon_converter, debounce_time_ms=300)

    # Wagon counter
    wagon_counter = SchmittConverter(
        wagon_detector,
        trigger_threshold=config[str(gpio_number)]["reflect"],
        release_threshold=config[str(gpio_number)]["open"],
    )
    wagon_count_debouncer = DebounceBehaviour(wagon_counter, debounce_time_ms=min_trigger_interval)
    wagon_count_events = EventOnChangeBehaviour(wagon_count_debouncer)

    return wagon_debouncer, wagon_count_events


sensors = {}
sensors["EOT_P"] = create_end_of_track_sensor(21)
sensors["POINT_BASE_P"], sensors["POINT_BASE_C"] = create_wagon_sensors(26)
sensors["POINT_THROUGH_P"], sensors["POINT_THROUGH_C"] = create_wagon_sensors(27)
sensors["POINT_DIVERGE_P"], sensors["POINT_DIVERGE_C"] = create_wagon_sensors(28)
