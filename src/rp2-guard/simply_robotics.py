"""
Encapsulates the control of robotic motors.

A module to provide the functionality of the Kitronik 5348 Simply Robotics board.
http://www.kitronik.co.uk/5348

The motors are connected as:
    Motor 1 -> GP2 + GP5
    Motor 2 -> GP4 + GP3
    Motor 3 -> GP6 + GP9
    Motor 4 -> GP8 + GP7

The servo pins are 15, 14, 13, 12, 19, 18, 17, 16 for servo 0 -> servo 7.
The numbers look strange but it makes the tracking on the PCB simpler and is hidden inside this lib.

Unused pins or GPIO breakouts are 21, 22, 26, 27, 28.

Derived from SimplyRobotics.py at https://github.com/KitronikLtd/Kitronik-Pico-Simply-Robotics-MicroPython
under the MIT License.
"""

from machine import PWM, Pin

MOTOR_CONNECTIONS = [
    (2, 5),
    (4, 3),
    (6, 9),
    (8, 7),
]


class Direction:
    """A direction enum for motors."""

    FORWARD = 1
    NEUTRAL = 0
    REVERSE = -1


class PWM_Motor:
    """A motor controlled using PWM."""

    def __init__(self, motor_number, frequency, scale_max_speed=1.0):
        """
        Create a new motor from the given motor number (1-4).

        The base frequency of the PWM signal - depends on motor type.
        The maximum speed can be reduced by setting scale_max_speed to (0.0-1.0).
        Coreless motors should set frequency to 20_000 Hz.
        """
        forwardPin, reversePin = MOTOR_CONNECTIONS[motor_number]

        self.forwardPin = PWM(Pin(forwardPin))
        self.reversePin = PWM(Pin(reversePin))
        self.scale_max_speed = scale_max_speed
        self.frequency = frequency
        self.forwardPin.freq(frequency)
        self.reversePin.freq(frequency)

        self.off()

    def on(self, direction, speed=0.0):
        """
        Set the motor to the given speed and direction.

        Speed is floating-point value between 0.0 and 1.0 inclusive.
        """
        # Restrict speed to 0.0 - 1.0
        speed = max(0.0, min(speed, 1.0))

        # Convert 0-1 to 0-65535
        pwmVal = int(speed * self.scale_max_speed * 65535)

        if direction == self.FORWARD:
            self.forwardPin.duty_u16(pwmVal)
            self.reversePin.duty_u16(0)

        elif direction == self.REVERSE:
            self.forwardPin.duty_u16(0)
            self.reversePin.duty_u16(pwmVal)

        elif direction == self.NEUTRAL:
            self.forwardPin.duty_u16(0)
            self.reversePin.duty_u16(0)

        else:
            raise RuntimeError(f"The provided direction '{direction}' is invalid.")

    def off(self):
        """Turn off motor, setting direction to neutral and speed to zero."""
        self.on(self.NEUTRAL, 0)


class DC_Motor(PWM_Motor):
    """A DC motor controller."""

    def __init__(self, motor_number, scale_max_speed=1.0, frequency=100):
        """Create a new DC motor from the given motor number (1-4)."""
        super(motor_number, scale_max_speed, frequency)


class CorelessMotor(PWM_Motor):
    """A coreless motor controller."""

    def __init__(self, motor_number, scale_max_speed=0.5, frequency=20_000):
        """Create a new coreless motor from the given motor number (1-4)."""
        super(motor_number, scale_max_speed, frequency)
