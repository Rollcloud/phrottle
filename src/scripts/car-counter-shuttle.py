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
from layout import AbsoluteDirection as Facing
from layout import Locomotive, Point

COUNT_THRESHOLD = 50
CLEAR_THRESHOLD = 70
FOUND_THRESHOLD = 90

MAX_SPEED = 500  # mm/s
MIN_WAGON_LENGTH = 25  # 1 inch in mm
REFLECTOR_LENGTH = 5  # mm

min_trigger_interval = int(MIN_WAGON_LENGTH / MAX_SPEED * 1000)  # 83 ms
min_trigger_duration = int(REFLECTOR_LENGTH / MAX_SPEED * 1000)  # 17 ms

point = Point(motor_number=1, id="Point")
loco = Locomotive(motor_number=0, id="test", orientation=Facing.RIGHT)
loco.profile["max_speed"] = 1  # set really slow for shuttle tests


def create_touch_sensor(gpio_number):
    touch_detector = DigitalDetector(gpio_number)
    touch_converter = SimpleThresholdConverter(touch_detector, threshold=1)
    touch_debouncer = DebounceBehaviour(touch_converter, debounce_time_ms=1000)
    touch_behaviour = EventOnChangeBehaviour(touch_debouncer)
    return touch_behaviour


# Touch sensor
touch_right = create_touch_sensor(0)
touch_left = create_touch_sensor(1)

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

    print("Press left or right touch sensor to start moving in that direction:")

    while True:
        if touch_left.check_event() == BehaviourEvent.TRIGGER:
            forward = False
            print("Moving backwards")
            break
        if touch_right.check_event() == BehaviourEvent.TRIGGER:
            forward = True
            print("Moving forwards")
            break
        utime.sleep_ms(100)

    try:
        while True:
            # Light LED when wagon is over sensor
            # led.value(wagon_debouncer.is_present())

            # Increment counter when wagon is detected
            event = wagon_count_events.check_event()
            if event == BehaviourEvent.TRIGGER:
                counts += 1
                led.toggle()
                print(counts, end="")
            elif event == BehaviourEvent.RELEASE:
                print(".")

            # Shuttle train over sensor
            if forward:
                loco.accelerate(0.2)
                if counts >= 2 and not wagon_debouncer.is_present():
                    loco.stop()
                    forward = False
                    counts = 0
            else:
                loco.accelerate(-0.2)
                if counts >= 2 and not wagon_debouncer.is_present():
                    loco.stop()
                    forward = True
                    counts = 0

            # Toggle point when touched
            touch_event = touch_right.check_event()
            if touch_event == BehaviourEvent.TRIGGER:
                # Do not toggle if wagon is present
                if wagon_debouncer.is_present():
                    print("Wagon present, cannot toggle point.")
                else:
                    point.toggle()

            # Stop train when touched
            touch_event = touch_left.check_event()
            if touch_event == BehaviourEvent.TRIGGER:
                loco.stop()
                print("Emergency stop triggered")
                raise KeyboardInterrupt

            utime.sleep_ms(min_trigger_duration)
    except KeyboardInterrupt:
        loco.stop()
        point.off()
        led.off()
        print("Train stopped")
    except Exception:
        loco.stop()
        point.off()
        led.off()
        print("Train stopped")
