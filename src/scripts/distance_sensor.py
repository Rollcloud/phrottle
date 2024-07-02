from machine import Pin
import utime

sensor = Pin(28, Pin.IN)

while True:
    print(sensor.value(), end="\r") 
    utime.sleep_ms(10)
