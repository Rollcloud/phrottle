import utime
from machine import ADC
from SimplyRobotics import PIOServo  # type: ignore

servo = PIOServo(18)
servo.registerServo()

sensor = ADC(1)


def read_sensor():
    return sensor.read_u16() >> 6


try:
    while True:
        value = read_sensor() / 1024 * 180
        position = min(max(180 - value, 0), 180)

        print("value =", value, end="          \r")
        servo.goToPosition(position)
        utime.sleep(2)
finally:
    servo.deregisterServo()
