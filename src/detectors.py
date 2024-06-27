from machine import ADC


class AnalogueDetector:
    """A threshold detector for an analogue sensor."""

    DEFAULT_THRESHOLD = 2**10 / 2  # mid-point of 10-bit ADC

    def __init__(
        self, gpio_number, threshold=DEFAULT_THRESHOLD, filter_alpha=0.0, calibrate=False
    ) -> None:
        """
        Initialise an analogue sensor detector connected to the provided pin.

        Args:
            filter_alpha [0.0, 1.0]: lower is stronger
            calibrate: whether to set the sensor's base (untriggered) level on startup
        """
        self._gpio_number = gpio_number
        self._filter_alpha = filter_alpha
        self._sensor = ADC(gpio_number)

        self.threshold = threshold
        self.calibration = self.value() if calibrate else 0

    def value_raw(self) -> int:
        """Return the ADC value in bits."""
        return self._sensor.read_u16() >> 6  # 10-bit ADC

    def value(self) -> int:
        """Return the detector value including calibration (if enabled)."""
        return self.value_raw() - self.calibration

    def is_present(self) -> bool:
        """Return whether an object is present."""
        return self.value() < self.threshold


if __name__ == "__main__":
    import utime

    detector = AnalogueDetector(28, threshold=128)

    while True:
        is_present = detector.is_present()
        value = detector.value()
        # print(detector.value_raw(), value)
        print("O" if is_present else "-", end=" |")
        print(" " * (value // 4) + "X" + " " * 10, end="\r")

        utime.sleep_ms(50)
