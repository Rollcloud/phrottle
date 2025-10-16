"""Create host WiFi network."""

import utime
from hardware import LED, PWM_LED, CorelessMotor, Switch, WiFi
from stately import STATES, StateMachine

ACCELERATION = 3
WAIT_BEFORE_CHANGING_DIRECTION = 2000  # milliseconds
HOLD_BUTTON_UNTIL_START_AUTO = 800  # milliseconds

wifi = None
stop_switch = None
fwd_sensor = None
rev_sensor = None
wifi_led = None
speed_led = None
motor = None

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
    global wifi_led, wifi, speed_led, motor, fwd_sensor, rev_sensor, stop_switch

    wifi_led = LED()
    stop_switch = Switch(21)
    rev_sensor = Switch(26, pull=None)
    fwd_sensor = Switch(27, pull=None)
    speed_led = PWM_LED(16)
    motor = CorelessMotor(1)

    wifi = WiFi()
    wifi_led.pin.on()

    return STATES.CONNECT


def state_connect():
    """Connect state."""
    try:
        wifi.share_access_point()
        utime.sleep(0.5)
        wifi.open_udp_socket()
        utime.sleep(0.5)

        return STATES.STOP
    except Exception:
        return STATES.ERROR


def state_stop():
    """Stop state."""
    wifi_led.pin.toggle()
    speed_led.off()
    motor.off()

    wifi.send("STOPPED", wifi.broadcast)

    data = wifi.receive(include_ip_address=True)
    if data is None:
        return  # skip further parsing

    # start automatic mode, by holding down button
    if stop_switch.is_high():
        if future_ticks is None:
            future_ticks = utime.ticks_add(utime.ticks_ms(), HOLD_BUTTON_UNTIL_START_AUTO)
        elif utime.ticks_diff(future_ticks, utime.ticks_ms()) <= 0:
            future_ticks = None
            if stop_switch.is_high():  # if it's still high
                return STATES.BOUNCE
            else:
                pass  # Do nothing
        else:
            pass  # wait for time to pass...
    else:
        # reset hold timer
        future_ticks = None

    message, ip_address = data
    if b"MARCO" in message:
        wifi.send("POLO", ip_address)
    elif b"CONTROL" in message:
        return STATES.MANUAL
    elif b"AUTO" in message:
        return STATES.BOUNCE


def state_manual():
    """Manual state."""
    wifi_led.pin.on()

    if stop_switch.is_high():
        return STATES.STOP

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"CONTROL" in message:
        _control, direction, speed = message.split()  # eg: CONTROL F 100 --> forward full speed

        speed_led.on()
        speed_led.brightness(int(speed))
        motor.on(Direction.letter(direction), speed / 100)
    elif b"STOP" in message:
        return STATES.STOP


def state_forward():
    """Forward state."""
    global current_direction

    current_direction = Direction.FORWARD
    new_speed = speed_led.value + ACCELERATION

    speed_led.activate()
    speed_led.brightness(new_speed)
    motor.on(current_direction, new_speed / 100)

    wifi.send("FORWARD", wifi.broadcast)

    if stop_switch.is_high():
        return STATES.STOP
    if fwd_sensor.is_high():
        wifi.send("FORWARD_END", wifi.broadcast)
        return STATES.SLOW

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP


def state_reverse():
    """Reverse state."""
    global current_direction

    current_direction = Direction.REVERSE
    new_speed = speed_led.value + ACCELERATION

    speed_led.activate()
    speed_led.brightness(new_speed)
    motor.on(current_direction, new_speed / 100)

    wifi.send("REVERSE", wifi.broadcast)

    if stop_switch.is_high():
        return STATES.STOP
    if rev_sensor.is_high():
        wifi.send("REVERSE_END", wifi.broadcast)
        return STATES.SLOW

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP


def state_slow():
    """Slow to a stop."""
    new_speed = speed_led.value - ACCELERATION
    speed_led.brightness(new_speed)
    motor.on(current_direction, new_speed / 100)

    if speed_led.value == 0:
        return STATES.BOUNCE

    if stop_switch.is_high():
        return STATES.STOP

    if fwd_sensor.is_high() and rev_sensor.is_high():
        return STATES.ERROR

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP


def state_bounce():
    """Wait, then change direction."""
    global future_ticks, current_direction

    wifi_led.pin.off()

    wifi.send("BOUNCE", wifi.broadcast)

    if stop_switch.is_high():
        return STATES.STOP

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP

    if future_ticks is None:
        future_ticks = utime.ticks_add(utime.ticks_ms(), WAIT_BEFORE_CHANGING_DIRECTION)
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
    motor.off()

    wifi.send("ERROR", wifi.broadcast)

    if stop_switch.is_high():
        return STATES.STOP

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"STOP" in message:
        return STATES.STOP


def state_shutdown():
    """Shutdown state."""
    wifi_led.pin.off()
    speed_led.off()
    motor.off()

    wifi.close_udp_socket()
    wifi.disconnect_wifi()


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
