from time import sleep_ms

from lib.SimplyRobotics import SimplePWMMotor
from machine import ADC, Pin

FORWARD = "f"
REVERSE = "r"

CONVERSION_FACTOR = 3.3 / (65535)

led = Pin("LED", Pin.OUT)
motor = None
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
    temperature_sensor = ADC(4)

    reading = temperature_sensor.read_u16() * CONVERSION_FACTOR

    # The temperature sensor measures the Vbe voltage of a biased bipolar diode, connected to the fifth ADC channel
    # Typically, Vbe = 0.706V at 27 degrees C, with a slope of -1.721mV (0.001721) per degree.
    temperature = 27 - (reading - 0.706) / 0.001721
    return temperature


def init_motor():
    """Initialise a SimplePWMMotor."""
    global motor
    motor = SimplePWMMotor(2, 5, 100)


def motor_on(direction, percentage_vmax: float):
    """Provide a wrapper for `SimplePWMMotor.on`."""
    global motor
    if motor is None:
        raise Exception("Motor not initialised")
    motor.on(direction, percentage_vmax)


def motor_off():
    """Provide a wrapper for `SimplePWMMotor.off`."""
    global motor
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
