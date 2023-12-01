from time import sleep_ms

from machine import ADC, Pin

CONVERSION_FACTOR = 3.3 / (65535)

led = Pin("LED", Pin.OUT)


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
