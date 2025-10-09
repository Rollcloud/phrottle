# State machine module class.


class STATES:
    """State machine state constants."""

    POWER = 0
    CONNECT = 1
    IDENTIFY = 2
    MANUAL = 3
    AUTOMATIC = 4


class StateMachine:
    """
    State machine object class.

    Calls the appropriate function based on its current state.

    The functions should return a STATES enum to set the next state to enter.
    """

    def __init__(self, state_functions) -> None:
        self.state = 0  # first state in the states enum
        self.state_functions = state_functions

    def run_loop(self):
        """Execute the state machine functions in a loop."""
        try:
            while True:
                print(self.state)  # TODO: remove debug print statement
                next_state = self.state_functions[self.state]()
                self.state = next_state or self.state
        except KeyboardInterrupt:
            pass  # Keyboard interrupt is an expected way to interrupt the state machine
