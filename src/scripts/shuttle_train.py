from detectors import AnalogueDetector
from layout import AbsoluteDirection as facing
from layout import Locomotive, Point
from machine import Pin
from scheduler import Scheduler

LOW_FREQUENCY_PERIOD_MS = 100
SENSORS_PERIOD_MS = 10

up_time = 0  # ms
wait_trigger = None
wait_flag = False

led = Pin("LED", Pin.OUT)
detector = AnalogueDetector(28, threshold=128)

engine = Locomotive(motor_number=0, id="test", orientation=facing.RIGHT)
engine.profile["max_speed"] = 3  # set really slow for shuttle tests

point = Point(motor_number=1, id="Point", through_is_forward=True)

event_queue = []


class Events:
    """State machine event constants."""

    SYSTEM_STOP = 0
    TRAIN_DETECTED = 1
    TRAIN_UNDETECTED = 2
    SHUTTLE_START = 3
    SHUTTLE_STOP = 4
    TASK_COMPLETE = 5


def home_ready():
    engine.stop()
    event_queue.append(Events.SHUTTLE_START)


def home_start():
    engine.accelerate(0.1)
    if wait_for(2500):
        event_queue.append(Events.SHUTTLE_STOP)


def away_stop():
    engine.brake(0.25)
    if wait_for(3500):
        event_queue.append(Events.SHUTTLE_START)


def away_start():
    engine.accelerate(-0.1)
    if detector.is_present():
        event_queue.append(Events.TRAIN_DETECTED)


def home_stop():
    if engine.speed > 1.6:
        engine.brake(1.5)
    if detector.is_present() is False:
        engine.stop()
        event_queue.append(Events.TRAIN_UNDETECTED)


def change_point():
    point.toggle()
    event_queue.append(Events.TASK_COMPLETE)


def point_changing():
    if wait_for(3000):
        event_queue.append(Events.TASK_COMPLETE)


state_machine = {
    # state: (callback, {event: state})
    "home_ready": {Events.SHUTTLE_START: "home_start"},
    "home_start": {Events.SHUTTLE_STOP: "away_stop"},
    "away_stop": {Events.SHUTTLE_START: "away_start"},
    "away_start": {Events.TRAIN_DETECTED: "home_stop"},
    "home_stop": {Events.TRAIN_UNDETECTED: "change_point"},
    "change_point": {Events.TASK_COMPLETE: "point_changing"},
    "point_changing": {Events.TASK_COMPLETE: "home_ready"},
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


def wait_for(milliseconds):
    """Wait for the given number of milliseconds before returning True."""
    global wait_trigger, wait_flag

    if wait_trigger is None:
        wait_trigger = up_time + milliseconds
    elif wait_flag:
        wait_flag = False
        wait_trigger = None
        return True

    return False


def sensors_loop():
    global detector
    present = detector.is_present()
    led.value(1 if present else 0)
    # print(f"{detector.value(): 3d} {present}", end="")


def low_frequency_loop(ticks_delta):
    global up_time, state, wait_trigger, wait_flag
    up_time += ticks_delta

    if wait_trigger and up_time >= wait_trigger:
        wait_flag = True

    state = run_state_machine(state)

    wait_str = f"wait={((wait_trigger - up_time) / 1000 if wait_trigger else 0.0):.1f}s"

    print(
        f"state={state}, velocity={engine.velocity:.1f} events={event_queue} {wait_str}",
        end="    \r",
    )


sensors_scheduler = Scheduler(SENSORS_PERIOD_MS)
lf_scheduler = Scheduler(LOW_FREQUENCY_PERIOD_MS)

try:
    while True:
        if sensors_scheduler.is_ready():
            sensors_loop()

        if lf_scheduler.is_ready():
            low_frequency_loop(lf_scheduler.delta)

except KeyboardInterrupt:
    print("Keyboard exit detected")
finally:
    led.off()
    engine.stop()
