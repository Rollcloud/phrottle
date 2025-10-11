"""Create host WiFi network."""

import utime
from hardware import LED, PWM_LED, WiFi
from stately import STATES, StateMachine

ACCELERATION = 3

wifi = None
wifi_led = None
speed_led = None

current_speed = 0
current_direction = None
future_ticks = None


class Direction:
    """A numeric representation of the direction."""

    REVERSE = -1
    NONE = 0
    FORWARD = 1

    @staticmethod
    def letter(direction):
        letters = {
            -1: "R",
            0: "N",
            1: "F",
        }
        return letters[direction]


def send_state():
    pass


def state_initialise():
    """Initialise state."""
    global wifi_led, wifi, speed_led

    wifi_led = LED()
    speed_led = PWM_LED(16)

    wifi = WiFi()
    wifi_led.pin.on()

    return STATES.CONNECT


def state_connect():
    """Connect state."""
    try:
        wifi.share_access_point()
        wifi_led.pin.off()
        wifi.open_connection()
        wifi_led.pin.on()

        return STATES.STOP
    except Exception:
        return STATES.ERROR


def state_stop():
    """Stop state."""
    speed_led.off()

    wifi.send("STOPPED", wifi.broadcast)

    while True:
        data = wifi.receive(include_ip_address=True)

        if not data:
            continue

        message, ip_address = data

        if b"CONTROL" in message:
            wifi.send("ECHO " + message.decode(), wifi.broadcast)
            _control, direction, speed = message.split()

            if direction == b"R":
                speed_led.on()
            elif direction == b"F":
                speed_led.off()

            speed_led.brightness(int(speed))

        elif b"AUTO" in message:
            return STATES.BOUNCE

        elif b"MARCO" in message:
            wifi.send("POLO", ip_address)


def state_manual():
    """Manual state."""


def state_forward():
    """Forward state."""
    global current_direction

    current_direction = Direction.FORWARD

    speed_led.activate()
    speed_led.brightness(speed_led.value + ACCELERATION)

    wifi.send("FORWARD", wifi.broadcast)

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP
    elif b"TRIGGER" in message:
        wifi.send("FORWARD_END", wifi.broadcast)
        return STATES.SLOW


def state_reverse():
    """Reverse state."""
    global current_direction

    current_direction = Direction.REVERSE

    speed_led.activate()
    speed_led.brightness(speed_led.value + ACCELERATION)

    wifi.send("REVERSE", wifi.broadcast)

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP
    elif b"TRIGGER" in message:
        wifi.send("REVERSE_END", wifi.broadcast)
        return STATES.SLOW


def state_slow():
    """Slow to a stop."""
    speed_led.brightness(speed_led.value - ACCELERATION)

    if speed_led.value == 0:
        return STATES.BOUNCE

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP


def state_bounce():
    """Wait, then change direction."""
    global future_ticks, current_direction

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP

    if future_ticks is None:
        future_ticks = utime.ticks_add(utime.ticks_ms(), 2000)
    elif utime.ticks_diff(future_ticks, utime.ticks_ms()) <= 0:
        future_ticks = None
        if current_direction == Direction.FORWARD:
            return STATES.REVERSE
        else:
            # Go forward by default
            return STATES.FORWARD
    else:
        pass  # wait for time to pass...


def state_error():
    """Error state."""
    speed_led.off()

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP


def state_shutdown():
    """Shutdown state."""
    wifi_led.pin.off()
    speed_led.off()

    wifi.close_connection()


if __name__ == "__main__":
    state_functions = {
        STATES.INITIALISE: state_initialise,
        STATES.CONNECT: state_connect,
        STATES.STOP: state_stop,
        STATES.MANUAL: state_manual,
        STATES.FORWARD: state_forward,
        STATES.REVERSE: state_reverse,
        STATES.SLOW: state_slow,
        STATES.BOUNCE: state_bounce,
        STATES.ERROR: state_error,
        STATES.SHUTDOWN: state_shutdown,
    }
    state_machine = StateMachine(state_functions, interrupt_state=STATES.SHUTDOWN)
    state_machine.run_loop()
