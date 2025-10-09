from machine import Pin


class Switch:
    """An ON-OFF input switch with an internal pull-up resistor."""

    def __init__(self, gpio) -> None:
        self.pin = Pin(gpio, Pin.IN, Pin.PULL_UP)

    def is_high(self):
        return 1 - self.pin.value()  # invert the value for pull-up resistor


class TriColourLED:
    """A RGB LED."""

    OFF = (0, 0, 0)
    RED = (1, 0, 0)
    YELLOW = (1, 1, 0)
    GREEN = (0, 1, 0)
    BLUE = (0, 0, 1)
    PURPLE = (1, 0, 1)
    WHITE = (1, 1, 1)

    def __init__(self, red_gpio, green_gpio, blue_gpio) -> None:
        self.red_pin = Pin(red_gpio, Pin.OUT)
        self.green_pin = Pin(green_gpio, Pin.OUT)
        self.blue_pin = Pin(blue_gpio, Pin.OUT)

        self.colour(self.OFF)

    def colour(self, new_colour):
        r, g, b = new_colour
        # invert the values for common anode
        self.red_pin.value(1 - r)
        self.green_pin.value(1 - g)
        self.blue_pin.value(1 - b)
