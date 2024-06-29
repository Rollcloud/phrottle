import utime
from detectors import (
    AGCConverter,
    AnalogueDetector,
    BehaviourEvent,
    DebounceBehaviour,
    DigitalDetector,
    EventOnChangeBehaviour,
    SchmittConverter,
    SimpleThresholdConverter,
)
from hardware import led
from layout import Point

COUNT_THRESHOLD = 50
CLEAR_THRESHOLD = 70
FOUND_THRESHOLD = 90

MAX_SPEED = 300  # mm/s
MIN_WAGON_LENGTH = 25  # 1 inch in mm
REFLECTOR_LENGTH = 5  # mm

min_trigger_interval = int(MIN_WAGON_LENGTH / MAX_SPEED * 1000)  # 83 ms
min_trigger_duration = int(REFLECTOR_LENGTH / MAX_SPEED * 1000)  # 17 ms

point = Point(motor_number=1, id="Point")

# Touch sensor
touch_detector = DigitalDetector(0)
touch_converter = SimpleThresholdConverter(touch_detector, threshold=1)
touch_debouncer = DebounceBehaviour(touch_converter, debounce_time_ms=1000)
touch_behaviour = EventOnChangeBehaviour(touch_debouncer)

# Wagon presence sensor
wagon_detector = AnalogueDetector(28)
wagon_converter = AGCConverter(wagon_detector, base_threshold=15, gain=0.05)
wagon_debouncer = DebounceBehaviour(wagon_converter, debounce_time_ms=100)

# Wagon counter
wagon_counter = SchmittConverter(
    wagon_detector, trigger_threshold=COUNT_THRESHOLD, release_threshold=CLEAR_THRESHOLD
)
wagon_count_debouncer = DebounceBehaviour(wagon_counter, debounce_time_ms=min_trigger_interval)
wagon_count_events = EventOnChangeBehaviour(wagon_count_debouncer)

counts = 0


if __name__ == "__main__":
    led.off()

    while True:
        # Light LED when wagon is over sensor
        led.value(wagon_debouncer.is_present())

        # Increment counter when wagon is detected
        event = wagon_count_events.check_event()
        if event == BehaviourEvent.TRIGGER:
            counts += 1
            print(counts, end="")
        elif event == BehaviourEvent.RELEASE:
            print(".")

        # Toggle point when touched
        touch_event = touch_behaviour.check_event()
        if touch_event == BehaviourEvent.TRIGGER:
            # Do not toggle if wagon is present
            if wagon_debouncer.is_present():
                print("Wagon present, cannot toggle point.")
            else:
                point.toggle()

        utime.sleep_ms(min_trigger_duration)
