import socket
import struct
from time import gmtime, sleep_ms, ticks_ms

from lib.SimplyRobotics import SimplePWMMotor
from machine import ADC, RTC, Pin

FORWARD = "f"
REVERSE = "r"

CONVERSION_FACTOR = 3.3 / (65535)

NTP_DELTA = 2208988800
NTP_HOST = "pool.ntp.org"
msec_offset = 0

rtc = RTC()
led = Pin("LED", Pin.OUT)
motors = {}
speaker = None


def flash_led(t: float = 0.12, n: int = 1):
    """[Blocking] Flash the LED for t seconds n times."""
    while n > 0:
        led.on()
        sleep_ms(int(t * 1000))
        led.off()
        if n > 1:
            sleep_ms(int(t * 1000))
        n -= 1


def get_internal_temperature():
    """Read the onboard temperature sensor."""
    temperature_sensor = ADC("GP4")

    reading = temperature_sensor.read_u16() * CONVERSION_FACTOR

    # The temperature sensor measures the Vbe voltage of a biased bipolar diode, connected to the fifth ADC channel
    # Typically, Vbe = 0.706V at 27 degrees C, with a slope of -1.721mV (0.001721) per degree.
    temperature = 27 - (reading - 0.706) / 0.001721
    return temperature


def set_rtc_time() -> None:
    # Get the external time reference
    global msec_offset
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(NTP_HOST, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(10)
        s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()

    # Set our internal time
    val = struct.unpack("!I", msg[40:44])[0]
    tm = val - NTP_DELTA
    t = gmtime(tm)
    rtc.datetime((t[0], t[1], t[2], t[6] + 1, t[3], t[4], t[5], 0))
    msec_offset = ticks_ms()


def get_iso_datetime() -> str:
    year, month, day, _dow, hour, mins, secs, _subsec = rtc.datetime()
    subsec = (ticks_ms() - msec_offset) % 1000
    return "{:04}-{:02}-{:02} {:02}:{:02}:{:02}.{:03}".format(
        year, month, day, hour, mins, secs, subsec
    )


def init_motor(number):
    """
    Initialise a SimplePWMMotor.

    Choose the motor number from the SimplyRobotics board.
    """
    global motors
    if number == 0:
        motors[0] = SimplePWMMotor(2, 5, 100)
    elif number == 1:
        motors[1] = SimplePWMMotor(4, 3, 100)
    elif number == 2:
        motors[2] = SimplePWMMotor(6, 9, 100)
    elif number == 3:
        motors[3] = SimplePWMMotor(8, 7, 100)


def motor_on(number, direction, percentage_vmax: float):
    """
    Provide a wrapper for `SimplePWMMotor.on`.

    Provide the motor number from the SimplyRobotics board.
    """
    global motors
    motor = motors.get(number)
    if motor is None:
        raise Exception("Motor not initialised")
    motor.on(direction, percentage_vmax)


def motor_off(number):
    """
    Provide a wrapper for `SimplePWMMotor.off`.

    Provide the motor number from the SimplyRobotics board.
    """
    global motors
    motor = motors.get(number)
    if motor is None:
        raise Exception("Motor not initialised")
    motor.off()


def init_speaker():
    global speaker
    speaker = Pin(6, Pin.OUT)


def speaker_on():
    global speaker
    if speaker is None:
        raise Exception("speaker not initialised")
    speaker.on()


def speaker_off():
    global speaker
    if speaker is None:
        raise Exception("speaker not initialised")
    speaker.off()


def click_speaker(t: float = 0.12, n: int = 1):
    """[Blocking] Click the speaker for t seconds n times."""
    global speaker
    if speaker is None:
        raise Exception("speaker not initialised")
    while n > 0:
        speaker.on()
        sleep_ms(int(t * 1000))
        speaker.off()
        if n > 1:
            sleep_ms(int(t * 1000))
        n -= 1
