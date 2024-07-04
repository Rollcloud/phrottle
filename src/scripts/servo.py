import utime
from SimplyRobotics import PIOServo  # type: ignore


position = 0  # degrees
velocity = 0  # degrees per second
acceleration = 50  # degrees per second squared

tick_period = 0.01  # seconds

servo = PIOServo(18)

servo.registerServo()

servo.goToPosition(0)

utime.sleep(1)

try:
    while True:
        velocity += acceleration * tick_period
        position += velocity

        # add bounce
        if position >= 180:
            velocity = -velocity * 0.6

        position = min(position, 180)

        print(position, end="          \r")
        servo.goToPosition(position)
        utime.sleep(tick_period)
finally:
    servo.deregisterServo()
