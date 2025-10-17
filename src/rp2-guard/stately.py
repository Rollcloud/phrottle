# State machine module class.


class STATES:
    """State machine state constants."""

    INITIALISE = 0
    CONNECT = 1
    STOP = 2
    MANUAL = 3
    FORWARD = 4
    REVERSE = 5
    SLOW = 6
    WAIT = 7
    BOUNCE = 8
    ERROR = 9
    SHUTDOWN = 10


class StateMachine:
    """
    State machine object class.

    Calls the appropriate function based on its current state.

    The functions should return a STATES enum to set the next state to enter.
    """

    def __init__(self, state_functions, on_before_state=None, interrupt_state=None) -> None:
        self.state = 0  # first state in the states enum
        self.state_functions = state_functions
        self.on_before_state = on_before_state
        self.interrupt_state = interrupt_state

    def run_loop(self):
        """Execute the state machine functions in a loop."""
        try:
            while True:
                print(f"state={self.state}")  # TODO: remove debug print statement
                if self.on_before_state:
                    self.on_before_state()
                next_state = self.state_functions[self.state]()
                self.state = next_state or self.state
        except KeyboardInterrupt:
            # Keyboard interrupt is an expected way to stop the state machine
            if self.interrupt_state:
                next_state = self.state_functions[self.interrupt_state]()
                self.state = next_state or self.state
