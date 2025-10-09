# A state-machine powered interface to provide control and feedback of semi-automatic layout control
#
# Feedback is in the form of two LEDS (Fwd and Rev) which can be either orange (fire), or blue (ice)


# States and behaviours
#
# Transitions:
#
# POWER -> CONNECT -> IDENTIFY -> MANUAL -> AUTOMATIC -> MANUAL
#
# -------------------------------------------------------------
#
# POWER
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


from hardware import TriColourLED
from stately import STATES, StateMachine

fwd_led = None
rev_led = None


def state_power():
    """Initialise hardware when power is first applied."""
    global fwd_led, rev_led

    fwd_led = TriColourLED(4, 2, 3)
    rev_led = TriColourLED(6, 7, 8)

    return STATES.CONNECT


def state_connect():
    """
    Connect to the WIFI network.

    - Both LEDs slow-fade orange
    - Connect to pre-configured WIFI network
    - Retry after 10 seconds, ad infinitum
    """
    fwd_led.colour(TriColourLED.RED)
    rev_led.colour(TriColourLED.RED)

    return STATES.IDENTIFY


def state_indentify():
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
    fwd_led.colour(TriColourLED.YELLOW)
    rev_led.colour(TriColourLED.YELLOW)

    fwd_led.colour(TriColourLED.GREEN)
    rev_led.colour(TriColourLED.GREEN)

    return STATES.MANUAL


def state_manual():
    """
    Provide manual control.

    - Check for feedback from destination
    - If any received, go to AUTOMATIC
    - Read speed and direction inputs
    - Set DIR LED to solid blue
    - Compare to current speed and direction
    - If different, send CONTROL update over UDP
    """
    fwd_led.colour(TriColourLED.OFF)
    rev_led.colour(TriColourLED.OFF)

    return STATES.AUTOMATIC


def state_automatic():
    """
    Respond to automatic control.

    - Both LEDs solid blue
    - Read speed and direction inputs
    - Compare to current speed and direction
    - If different, go to MANUAL
    """
    fwd_led.colour(TriColourLED.BLUE)
    rev_led.colour(TriColourLED.BLUE)

    return STATES.MANUAL


if __name__ == "__main__":
    state_functions = {
        STATES.POWER: state_power,
        STATES.CONNECT: state_connect,
        STATES.IDENTIFY: state_indentify,
        STATES.MANUAL: state_manual,
        STATES.AUTOMATIC: state_automatic,
    }
    state_machine = StateMachine(state_functions)
    state_machine.run_loop()
