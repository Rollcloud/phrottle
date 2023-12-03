try:
    import hardware
except Exception:
    # in normal python
    import mock_hardware as hardware


class AbsoluteDirection:
    """Direction when facing layout."""

    LEFT = 0  # nominal forward
    RIGHT = 1


class RelativeDirection:
    """Direction compared to movable object."""

    FORWARD = 0  # nominal forward
    REVERSE = 1


# direction locomotive moves when powered forwards
TRACK_POLARITY = AbsoluteDirection.LEFT


class Locomotive:
    """An instance of a locomotive containing a DC motor."""

    def __init__(self, orientation: int = AbsoluteDirection.LEFT) -> None:
        """
        Create a new locomotive instance.
        Orientation: AbsoluteDirection locomotive is facing
        """
        self.orientation = orientation
        self.velocity = 0  # units
        hardware.init_motor()

    def stop(self):
        self.velocity = 0
        self.set_motor_velocity()

    def _motion_direction(self):
        """Current direction of motion based on velocity."""
        return RelativeDirection.FORWARD if self.velocity >= 0 else RelativeDirection.REVERSE

    def _motion_speed(self):
        """Current speed of motion based on velocity."""
        return abs(self.velocity)

    def _set_motor_direct(self, locomotive_direction: int, speed: float):
        """
        Set motor RelativeDirection to locomotive orientation and speed in units.
        Will stop motor if steep is negative.
        Suggested for direct motor control.
        """
        if speed <= 0:
            hardware.motor_off()
            return
        direction_inversions = TRACK_POLARITY + self.orientation + locomotive_direction
        motor_direction = hardware.FORWARD if direction_inversions % 2 == 0 else hardware.REVERSE
        percentage = speed
        hardware.motor_on(motor_direction, percentage)

    def set_motor_velocity(self):
        """Set the motor to the locomotive's current velocity."""
        direction_inversions = TRACK_POLARITY + self.orientation + self._motion_direction()
        motor_direction = hardware.FORWARD if direction_inversions % 2 == 0 else hardware.REVERSE
        percentage = self._motion_speed()
        hardware.motor_on(motor_direction, percentage)

    def accelerate(self, amount: float = 0.2):
        """Accelerate at amount/s^2 where positive corresponds to forward."""
        self.velocity += amount
        self.set_motor_velocity()

    def brake(self, amount: float = 0.2):
        """Apply a deceleration of amount/s^2 to the current speed, stopping at zero."""
        speed = self._motion_speed()
        if amount >= speed:
            self.velocity = 0
            return
        speed -= amount
        self.velocity = speed * (1 if self._motion_direction() == RelativeDirection.FORWARD else -1)
        self.set_motor_velocity()

    class Evaluator:
        """A piece of railway bordered at each ingress by Train Detectors."""

        def __init__(self, name) -> None:
            self.name = name
            self.count = 0

        def add_count(self, amount: float):
            """
            Increment count of passing train cars.

            An amount of 0.5 can indicate a car occupying two evaluators simultaneously.
            """
            self.count += amount
            if self.count < 0:
                print(f"WARNING: Evaluator {self.name} has a negative count of {self.count}")

    class TrainDetector:
        """A simple detector to count passing train cars."""

        def __init__(self, name) -> None:
            self.name = name
            self.evaluator_left = None
            self.evaluator_right = None

        def register_evaluators(self, evaluator_left: Evaluator, evaluator_right: Evaluator):
            self.evaluator_left = evaluator_left
            self.evaluator_right = evaluator_right

        def trigger(self, absolute_direction):
            # left is positive
            amount = 0.5
            if absolute_direction == AbsoluteDirection.RIGHT:
                amount *= -1
            if self.evaluator_left:
                self.evaluator_left.add_count(amount)
            if self.evaluator_right:
                self.evaluator_right.add_count(-amount)
