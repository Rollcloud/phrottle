import utime

from lib.SimplyRobotics import SimplePWMMotor

FORWARD = "f"
REVERSE = "r"

motor = SimplePWMMotor(4, 3, 100)

print("Motor on")

motor.on(FORWARD, 100)
utime.sleep(3)
motor.off()

utime.sleep(1)

motor.on(REVERSE, 100)
utime.sleep(3)
motor.off()

utime.sleep(1)

print("Stopped")
