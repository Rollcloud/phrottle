# A state-machine powered interface to provide control and feedback of semi-automatic layout control
#
# Feedback is in the form of two LEDS (Fwd and Rev) which can be either orange (fire), or blue (ice)


# States and behaviours
#
# Transitions:
#
# INITIALISE -> CONNECT -> IDENTIFY -> MANUAL -> AUTOMATIC -> MANUAL
#   --> SHUTDOWN
#
# ------------------------------------------------------------------
#
# INITIALISE
#
# - Initialise hardware
#
# CONNECT
#
# - Both LEDs slow-fade orange
# - Connect to pre-configured WIFI network
# - Retry after 10 seconds, ad infinitum
#
# IDENTIFY
#
# - Both LEDs fast-fade orange
# - Send MARCO UDP message to broadcast address
# - Retry after 10 seconds, ad infinitum
# - Receive POLO UDP message with destination IP address
# - Save destination IP address
# - Both LEDs solid orange
# - Read speed and direction inputs and save as current
#
# MANUAL
#
# - Check for feedback from destination
# - If any received, go to AUTOMATIC
#
# - Read speed and direction inputs
# - Set DIR LED to solid blue
# - Compare to current speed and direction
# - If different, send CONTROL update over UDP
#
# AUTOMATIC
#
# - Both LEDs solid blue
# - Read speed and direction inputs
# - Compare to current speed and direction
# - If different, go to MANUAL
#
# SHUTDOWN
#
# Should shutdown state be triggered
# - Both LEDs off

from time import sleep

from hardware import Slider, Switch, TriColourLED, WiFi
from stately import STATES, StateMachine

fwd_led = None
rev_led = None

fwd_switch = None
rev_switch = None

speed_knob = None

wifi = None

last_speed = None
last_direction = None


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


def read_direction() -> Direction:
    """Read the direction switches and return the resulting Direction."""
    value = fwd_switch.is_high() - rev_switch.is_high()

    # TODO: convert to Direction constant

    return value


def state_initialise():
    """Initialise hardware when power is first applied."""
    global fwd_led, rev_led, fwd_switch, rev_switch, wifi, speed_knob

    fwd_led = TriColourLED(4, 2, 3)
    rev_led = TriColourLED(13, 12, 11)

    fwd_switch = Switch(14)
    rev_switch = Switch(15)

    speed_knob = Slider(28)

    wifi = WiFi()

    return STATES.CONNECT


def state_connect():
    """
    Connect to the WIFI network.

    - Both LEDs slow-fade orange
    - Connect to pre-configured WIFI network
    - Retry after 10 seconds, ad infinitum
    """
    fwd_led.colour(TriColourLED.OFF)
    rev_led.colour(TriColourLED.YELLOW)

    try:
        if wifi.connect():
            return STATES.IDENTIFY
    except Exception as e:
        print(e)
        pass  # Wait and try again

    sleep(10)


def state_identify():
    """
    Identify the destination address.

    - Both LEDs fast-fade orange
    - Send MARCO UDP message to broadcast address
    - Retry after 10 seconds, ad infinitum
    - Receive POLO UDP message with destination IP address
    - Save destination IP address
    - Both LEDs solid orange
    - Read speed and direction inputs and save as current
    """
    global last_speed, last_direction

    wifi.open_connection()

    while not wifi.receive_polo():
        fwd_led.toggle(TriColourLED.YELLOW, TriColourLED.BLUE)
        rev_led.toggle(TriColourLED.BLUE, TriColourLED.YELLOW)

        if wifi.wlan.status() != 3:
            return STATES.CONNECT

        wifi.send_marco()

    last_speed = speed_knob.value()
    last_direction = read_direction()

    return STATES.STOPPED


def state_stopped():
    """Reset now that automatic control has ended."""
    fwd_led.colour(TriColourLED.YELLOW)
    rev_led.colour(TriColourLED.YELLOW)

    new_speed = speed_knob.value()
    if new_speed >= 33 and new_speed <= 66:
        return STATES.TRANSITION


def state_transition():
    """Transition to manual or automatic."""
    global last_speed, last_direction

    fwd_led.colour(TriColourLED.PURPLE)
    rev_led.colour(TriColourLED.PURPLE)

    new_speed = speed_knob.value()
    last_speed = new_speed

    if new_speed == 0:
        return STATES.MANUAL
    elif new_speed == 100:
        wifi.send("AUTO")

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"BOUNCE" in message:
        return STATES.AUTOMATIC


def state_manual():
    """
    Provide manual control.

    - Check for feedback from destination
    - If any received, go to AUTOMATIC
    - Read speed and direction inputs
    - Set DIR LED to solid orange
    - Compare to current speed and direction
    - If different, send CONTROL update over UDP
    """
    global last_speed, last_direction

    new_speed = speed_knob.value()
    new_direction = read_direction()

    if new_direction == Direction.FORWARD:
        fwd_led.colour(TriColourLED.YELLOW)
        rev_led.colour(TriColourLED.OFF)
    elif new_direction == Direction.REVERSE:
        fwd_led.colour(TriColourLED.OFF)
        rev_led.colour(TriColourLED.YELLOW)
    else:
        fwd_led.colour(TriColourLED.OFF)
        rev_led.colour(TriColourLED.OFF)

    if fwd_switch.is_high() + rev_switch.is_high() == 2:
        wifi.send("STOP")
        return STATES.STOPPED
    elif new_direction != last_direction or new_speed != last_speed:
        message = f"CONTROL {Direction.letter(new_direction)} {new_speed}"
        wifi.send(message)

    sleep(0.02)

    last_direction = new_direction
    last_speed = new_speed

    return STATES.MANUAL


def state_automatic():
    """
    Respond to automatic control.

    - Both LEDs solid blue
    - Read speed and direction inputs
    - Compare to current speed and direction
    - If different, go to MANUAL
    """
    global last_speed, last_direction

    message = wifi.receive()
    if message is None:
        pass  # skip further parsing
    elif b"FORWARD_END" in message:
        fwd_led.colour(TriColourLED.YELLOW)
        rev_led.colour(TriColourLED.BLUE)
    elif b"REVERSE_END" in message:
        fwd_led.colour(TriColourLED.BLUE)
        rev_led.colour(TriColourLED.YELLOW)
    elif b"STOPPED" in message:
        return STATES.STOPPED
    else:
        fwd_led.colour(TriColourLED.BLUE)
        rev_led.colour(TriColourLED.BLUE)

    new_speed = speed_knob.value()
    new_direction = read_direction()

    if new_direction != Direction.NONE:
        wifi.send("TRIGGER")

    if abs(new_speed - last_speed) >= 2:
        wifi.send("STOP")


def state_shutdown():
    """Turn off hardware."""
    fwd_led.colour(TriColourLED.OFF)
    rev_led.colour(TriColourLED.OFF)

    wifi.close_connection()


if __name__ == "__main__":
    state_functions = {
        STATES.INITIALISE: state_initialise,
        STATES.CONNECT: state_connect,
        STATES.IDENTIFY: state_identify,
        STATES.STOPPED: state_stopped,
        STATES.TRANSITION: state_transition,
        STATES.MANUAL: state_manual,
        STATES.AUTOMATIC: state_automatic,
        STATES.SHUTDOWN: state_shutdown,
    }
    state_machine = StateMachine(state_functions, interrupt_state=STATES.SHUTDOWN)
    state_machine.run_loop()
