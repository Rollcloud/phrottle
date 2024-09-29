import utime
from detectors import (  # type: ignore
    AGCConverter,
    AnalogueDetector,
    DebounceBehaviour,
    DigitalDetector,
    EventOnChangeBehaviour,
    InverterBehaviour,
    SchmittConverter,
    SimpleThresholdConverter,
)

COUNT_THRESHOLD = 45
CLEAR_THRESHOLD = 160
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
        wagon_detector, trigger_threshold=COUNT_THRESHOLD, release_threshold=CLEAR_THRESHOLD
    )
    wagon_count_debouncer = DebounceBehaviour(wagon_counter, debounce_time_ms=min_trigger_interval)
    wagon_count_events = EventOnChangeBehaviour(wagon_count_debouncer)

    return wagon_debouncer, wagon_count_events


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

while True:
    # for sensors ending in P, print the sensor value
    for sensor_name, sensor in sensors.items():
        if sensor_name.endswith("_P"):
            print(f"{sensor_name}: {sensor.is_present()}")
    print("----------------")
    utime.sleep(0.1)
