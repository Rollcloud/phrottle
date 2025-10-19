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

from hardware import LED, Indicator, Slider, Switch, WiFi
from stately import STATES, StateMachine

fwd_indicator = None
rev_indicator = None

fwd_switch = None
rev_switch = None

speed_knob = None

wifi = None

last_speed = None
last_direction = None

direction_change_counter = 0  # Used for changing between manual and auto mode


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
    value = 1 if fwd_switch.is_high() else -1  # forward or reverse from a single switch

    # TODO: convert result to Direction constant
    return value


def before_state():
    """For execution after the state function."""
    try:
        fwd_indicator.show_guise(fwd_indicator.guise, effect="flicker")
        rev_indicator.show_guise(fwd_indicator.guise, effect="flicker")
    except AttributeError:
        # indicators have not been initialised yet
        pass


def state_initialise():
    """Initialise hardware when power is first applied."""
    global fwd_indicator, rev_indicator, fwd_switch, rev_switch, wifi, speed_knob

    fwd_indicator = Indicator(10, 13, 12)
    rev_indicator = Indicator(21, 18, 19)

    fwd_switch = Switch(17)
    # rev_switch = Switch(16)

    speed_knob = Slider(27)

    LED(11).pin.on()  # enable fwd_indicator
    LED(20).pin.on()  # enable rev_indicator
    LED(26).pin.on()  # enable speed_knob

    wifi = WiFi()

    return STATES.CONNECT


def state_connect():
    """
    Connect to the WIFI network.

    - Both LEDs slow-fade orange
    - Connect to pre-configured WIFI network
    - Retry after 10 seconds, ad infinitum
    """
    fwd_indicator.show_guise(Indicator.OFF)
    rev_indicator.show_guise(Indicator.ORANGE)

    try:
        if wifi.connect_to_wifi():
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

    wifi.open_udp_socket()

    # Put Guard into STOP state so that it can respond o the Marco Polo request
    wifi.send("STOP", wifi.broadcast)

    while not wifi.receive_polo():
        fwd_indicator.toggle(Indicator.ORANGE, Indicator.BLUE)
        rev_indicator.toggle(Indicator.BLUE, Indicator.ORANGE)

        if wifi.wlan.status() != 3:
            return STATES.CONNECT

        wifi.send_marco()

    last_speed = speed_knob.value()
    last_direction = read_direction()

    return STATES.STOPPED


def state_stopped():
    """Reset now that automatic control has ended."""
    fwd_indicator.show_guise(Indicator.ORANGE)
    rev_indicator.show_guise(Indicator.ORANGE)

    new_speed = speed_knob.value()
    if new_speed >= 33 and new_speed <= 66:
        return STATES.TRANSITION


def state_transition():
    """Transition to manual or automatic."""
    global last_speed, last_direction

    fwd_indicator.show_guise(Indicator.PURPLE)
    rev_indicator.show_guise(Indicator.PURPLE)

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
    global last_speed, last_direction, direction_change_counter

    new_speed = speed_knob.value()
    new_direction = read_direction()

    if new_direction == Direction.FORWARD:
        fwd_indicator.show_guise(Indicator.ORANGE)
        rev_indicator.show_guise(Indicator.OFF)
    elif new_direction == Direction.REVERSE:
        fwd_indicator.show_guise(Indicator.OFF)
        rev_indicator.show_guise(Indicator.ORANGE)
    else:
        fwd_indicator.show_guise(Indicator.OFF)
        rev_indicator.show_guise(Indicator.OFF)

    if new_speed == 0 and new_direction != last_direction:
        direction_change_counter += 1
    if new_speed > 0:
        direction_change_counter = 0

    if direction_change_counter >= 4:
        direction_change_counter = 0
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
        fwd_indicator.show_guise(Indicator.ORANGE)
        rev_indicator.show_guise(Indicator.BLUE)
    elif b"REVERSE_END" in message:
        fwd_indicator.show_guise(Indicator.BLUE)
        rev_indicator.show_guise(Indicator.ORANGE)
    elif b"STOPPED" in message:
        return STATES.STOPPED
    else:
        fwd_indicator.show_guise(Indicator.BLUE)
        rev_indicator.show_guise(Indicator.BLUE)

    new_speed = speed_knob.value()
    new_direction = read_direction()

    if new_direction != Direction.NONE:
        wifi.send("TRIGGER")

    if abs(new_speed - last_speed) >= 2:
        wifi.send("STOP")


def state_shutdown():
    """Turn off hardware."""
    fwd_indicator.show_guise(Indicator.OFF)
    rev_indicator.show_guise(Indicator.OFF)

    wifi.close_udp_socket()
    wifi.disconnect_wifi()


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
    state_machine = StateMachine(
        state_functions, on_before_state=before_state, interrupt_state=STATES.SHUTDOWN
    )
    state_machine.run_loop()
