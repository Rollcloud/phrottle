import utime
from machine import ADC
from SimplyRobotics import PIOServo

servo = PIOServo(18)
servo.registerServo()

sensor = ADC("GP0")


def read_sensor():
    return sensor.read_u16() >> 7


class PID:
    """A simple PID controller."""

    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.error = 0
        self.integral = 0
        self.derivative = 0
        self.last_error = 0

    def update(self, error):
        self.error = error
        self.integral += self.error
        self.derivative = self.error - self.last_error
        self.last_error = self.error

        return self.kp * self.error + self.ki * self.integral + self.kd * self.derivative


LIMIT_PER_STEP = 2.0  # degrees per step
controller = PID(0.15, 0.02, 0.05)
y = None

try:
    while True:
        value = read_sensor() / 256 * 180
        position = 180 - value

        if y is None:
            y = position

        error = position - y
        y += min(max(controller.update(error), -LIMIT_PER_STEP), LIMIT_PER_STEP)
        y = min(max(y, 0), 180)  # limit to 0-180 degrees

        print("value =", value, "position =", position, "y =", y, end="          \r")
        servo.goToPosition(y)
        utime.sleep(0.01)
finally:
    servo.deregisterServo()
