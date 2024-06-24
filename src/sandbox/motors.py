import utime

from lib.SimplyRobotics import SimplePWMMotor

FORWARD = "f"
REVERSE = "r"

motor = SimplePWMMotor(2, 5, 100)

print("Motor on")

motor.on(FORWARD, 10)
utime.sleep(0.5)
motor.off()

utime.sleep(1)

motor.on(REVERSE, 10)
utime.sleep(0.5)
motor.off()

utime.sleep(1)

print("Stopped")
