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

# motor steps per unit velocity
STEPS_PER_UNIT = 1

LOCOMOTIVE_PROFILES = {
    "test": {"start_step_forward": 8, "start_step_reverse": 9, "max_speed": 12},
    "lourie": {"start_step_forward": 7, "start_step_reverse": 8, "max_speed": 30},
}


class Locomotive:
    """An instance of a locomotive containing a DC motor."""

    def __init__(self, motor_number, id=None, orientation: int = AbsoluteDirection.LEFT) -> None:
        """
        Create a new locomotive instance.

        Args:
            motor_number (int): Number of motor from SimplyRobotics board.
            ID (str): Name of profile to apply to locomotive.
            Orientation (AbsoluteDirection): Direction the locomotive is facing.
        """
        self.motor_number = motor_number
        self.id = id.lower() if id else None
        self.profile = LOCOMOTIVE_PROFILES[self.id] if self.id else {}
        self.orientation = orientation
        self.velocity = 0  # units
        self.velocity_direction = self.orientation
        self._motor_step = 0
        self._motor_dir = hardware.FORWARD
        hardware.init_motor(motor_number)

    def stop(self):
        self.velocity = 0
        self._set_motor_step()

    @property
    def speed(self):
        """Return current speed of motion based on velocity."""
        return abs(self.velocity)

    def movement_direction(self):
        """Return current absolute direction of motion."""
        LEFT = AbsoluteDirection.LEFT
        RIGHT = AbsoluteDirection.RIGHT
        FORWARD = RelativeDirection.FORWARD

        velocity_direction = self.velocity_direction
        if self.orientation == LEFT:
            return LEFT if velocity_direction == FORWARD else RIGHT
        else:
            return RIGHT if velocity_direction == FORWARD else LEFT

    def _set_motor(self):
        """
        Set motor to motor step and direction.

        Will stop motor if step is negative.
        """
        if self._motor_step <= 0:
            hardware.motor_off(self.motor_number)
        else:
            hardware.motor_on(self.motor_number, self._motor_dir, self._motor_step)

    def _set_motor_step(self):
        """Set the motor step from the locomotive's current velocity."""
        direction_inversions = TRACK_POLARITY + self.orientation + self.velocity_direction
        self._motor_dir = hardware.FORWARD if direction_inversions % 2 == 0 else hardware.REVERSE

        speed = self.speed

        if self.velocity > 0:
            # moving forwards
            min_step = self.profile.get("start_step_forward", 5)
        elif self.velocity < 0:
            # moving in reverse
            min_step = self.profile.get("start_step_reverse", 5)
        else:
            # not moving
            min_step = 0

        self._motor_step = min_step + speed * STEPS_PER_UNIT
        self._set_motor()

    def accelerate(self, amount: float = 0.2):
        """Accelerate at amount/s^2 where positive corresponds to forward."""
        new_velocity = self.velocity + amount
        if new_velocity < 0:
            self.velocity = max(new_velocity, -self.profile.get("max_speed", 100))
        else:
            self.velocity = min(new_velocity, self.profile.get("max_speed", 100))

        if self.velocity > 0:
            self.velocity_direction = RelativeDirection.FORWARD
        if self.velocity < 0:
            self.velocity_direction = RelativeDirection.REVERSE

        self._set_motor_step()

    def brake(self, amount: float = 0.2):
        """Apply a deceleration of amount/s^2 to the current speed, stopping at zero."""
        speed = self.speed
        if amount >= speed:
            self.velocity = 0
        else:
            speed -= amount
            self.velocity = speed * (
                1 if self.velocity_direction == RelativeDirection.FORWARD else -1
            )
        self._set_motor_step()


class PointState:
    """State of a set of points on the railway."""

    THROUGH = 0
    DIVERGING = 1


class Point:
    """A point on the railway that can be switched."""

    def __init__(self, motor_number, id, through_is_forward=True) -> None:
        self.id = id
        self._diverging = False
        self.motor_number = motor_number
        self.through_direction = hardware.FORWARD if through_is_forward else hardware.REVERSE
        self.diverging_direction = hardware.REVERSE if through_is_forward else hardware.FORWARD

        hardware.init_motor(motor_number)

    def change(self, diverging: bool):
        """
        Change the point to the given state.

        Note that there will be about a 3 second delay before the point change has been completed.
        """
        if self.motor_number:
            direction = self.diverging_direction if diverging else self.through_direction
            hardware.motor_on(self.motor_number, direction, 100)

        self._diverging = diverging

    def toggle(self):
        """Toggle the point between diverging and through."""
        self.change(not self._diverging)

    def off(self):
        """Turn off the point motor."""
        if self.motor_number:
            hardware.motor_off(self.motor_number)

    def state(self):
        """Return the current state of the point."""
        return PointState.DIVERGING if self._diverging else PointState.THROUGH

    def is_diverging(self):
        """Return whether the point is currently diverging."""
        return self._diverging

    def is_through(self):
        """Return whether the point is currently through."""
        return not self._diverging


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

        print(f"Evaluator {self.name} count: {self.count}")


class TrainDetector:
    """A simple detector to count passing train cars."""

    def __init__(self, name) -> None:
        self.name = name
        self.evaluator_left = None
        self.evaluator_right = None

    def register_evaluators(self, evaluator_left, evaluator_right):
        self.evaluator_left = evaluator_left
        self.evaluator_right = evaluator_right

    def trigger(self, absolute_direction):
        """Call this function with a direction on a detector changing level."""
        # left is positive
        amount = 0.5
        if absolute_direction == AbsoluteDirection.RIGHT:
            amount *= -1
        if self.evaluator_left:
            self.evaluator_left.add_count(amount)
        if self.evaluator_right:
            self.evaluator_right.add_count(-amount)
