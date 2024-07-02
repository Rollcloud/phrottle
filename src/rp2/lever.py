import machine

ADC_OUTPUT_BITS = 16
ADC_ENOB = 9  # https://pico-adc.markomo.me/ENOB/
CONVERSION_FACTOR = (1 << ADC_ENOB) / (1 << ADC_OUTPUT_BITS)


class Lever:
    """A class representing a physical lever connected to an ADC pin."""

    PIN_ADC_MAP = {
        26: 0,
        27: 1,
        28: 2,
    }

    def __init__(self, pin, max_raw=512, max_out=100, filter_alpha=0.0) -> None:
        """Initialise Lever connected to the provided pin."""
        self._pin = pin
        self._max_raw = max_raw
        self._max_out = max_out
        self._filter_alpha = filter_alpha
        machine.Pin(pin, machine.Pin.IN)
        self._sensor = machine.ADC(Lever.PIN_ADC_MAP[pin])

    def _filter(self, x, alpha: float) -> float:
        try:
            y = alpha * x + (1 - alpha) * self.y_last
        except AttributeError:
            # self.y_last not defined
            y = x

        self.y_last = y
        return y

    def read(self) -> float:
        """Read the latest value from the lever, filtering the result."""
        reading = self._sensor.read_u16() * CONVERSION_FACTOR
        filtered_value = self._filter(reading, self._filter_alpha)
        limited_value = max(0, self._max_raw - filtered_value)
        scaled_value = limited_value * self._max_out / self._max_raw
        return scaled_value
