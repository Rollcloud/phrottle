from detectors import AnalogueDetector
from layout import AbsoluteDirection as facing
from layout import Locomotive
from machine import Pin
from scheduler import Scheduler

LOW_FREQUENCY_PERIOD_MS = 100
SENSORS_PERIOD_MS = 10

up_time = 0  # ms

led = Pin("LED", Pin.OUT)
detector = AnalogueDetector(28, threshold=128)

engine = Locomotive(motor_number=0, id="test", orientation=facing.RIGHT)
engine.profile["max_speed"] = 3  # set really slow for shuttle tests

event_queue = []


class Events:
    """State machine event constants."""

    SYSTEM_STOP = 0
    TRAIN_DETECTED = 1
    SHUTTLE_START = 2
    SHUTTLE_STOP = 3


def home_stop():
    engine.brake(1.5)


def home_ready():
    global countdown
    countdown = 3 * 10  # counts at 10 per second

    engine.stop()


def home_start():
    global countdown
    countdown -= 1
    if countdown < 0:
        event_queue.append(Events.SHUTTLE_STOP)

    engine.accelerate(0.1)


def away_stop():
    engine.brake(0.25)


def away_start():
    engine.accelerate(-0.1)


state_machine = {
    # state: (callback, {event: state})
    "home_stop": {Events.SHUTTLE_START: "home_ready"},
    "home_ready": {Events.TRAIN_DETECTED: "home_start"},
    "home_start": {Events.SHUTTLE_STOP: "away_stop"},
    "away_stop": {Events.SHUTTLE_START: "away_start"},
    "away_start": {Events.TRAIN_DETECTED: "home_stop"},
}
state = "home_ready"


def run_state_machine(state):
    event_state_mapping = state_machine[state]
    callback = locals()[state]
    callback()
    try:
        event = event_queue.pop(0)
    except IndexError:
        # no events in queue
        event = -1
    try:
        return event_state_mapping[event]
    except KeyError:
        # event is not in event_state_mapping
        return state


def sensors_loop():
    global detector
    present = detector.is_present()
    led.value(1 if present else 0)
    # print(f"{detector.value(): 3d} {present}", end="")


def low_frequency_loop(ticks_delta):
    global up_time, state, detector
    up_time += ticks_delta

    if detector.is_present():
        event_queue.append(Events.TRAIN_DETECTED)
        state = run_state_machine(state)  # run an additional time to handle the event
        print(
            f"state={state}, velocity={engine.velocity:.1f} events={event_queue}",
            end="    \r",
        )

    state = run_state_machine(state)

    print(
        f"state={state}, velocity={engine.velocity:.1f} events={event_queue}",
        end="    \r",
    )


sensors_scheduler = Scheduler(SENSORS_PERIOD_MS)
lf_scheduler = Scheduler(LOW_FREQUENCY_PERIOD_MS)
shuttle_scheduler = Scheduler(20 * 1000)

try:
    while True:
        if sensors_scheduler.is_ready():
            sensors_loop()

        if lf_scheduler.is_ready():
            low_frequency_loop(lf_scheduler.delta)

        if shuttle_scheduler.is_ready():
            event_queue.append(Events.SHUTTLE_START)

except KeyboardInterrupt:
    print("Keyboard exit detected")
finally:
    led.off()
    engine.stop()
