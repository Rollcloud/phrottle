import utime
from machine import Pin

sensor = Pin(28, Pin.IN)

while True:
    print(sensor.value(), end="\r")
    utime.sleep_ms(10)
