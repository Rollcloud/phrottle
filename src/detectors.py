import utime
from machine import ADC, Pin


class DetectorEvent:
    """Events that can be triggered by a detector."""

    NONE = 0
    TRIGGER = 1
    RELEASE = 2


class Detector:
    """A base class for detectors providing common functionality."""

    def value(self) -> int:
        """Return the detector value."""
        raise NotImplementedError

    def is_present(self) -> bool:
        """Return whether an object is present."""
        raise NotImplementedError


class AnalogueDetector(Detector):
    """A basic detector for an analogue sensor."""

    DEFAULT_THRESHOLD = 2**10 / 2  # mid-point of 10-bit ADC

    def __init__(self, gpio_number, simple_threshold=DEFAULT_THRESHOLD) -> None:
        """Initialise an analogue sensor detector connected to the provided pin."""
        self.gpio_number = gpio_number
        self._sensor = ADC(gpio_number)
        self._simple_threshold = simple_threshold

    def value_raw(self) -> int:
        """Return the ADC value in bits."""
        return self._sensor.read_u16() >> 6  # 10-bit ADC

    def value(self) -> int:
        """Return the detector value."""
        return self.value_raw()

    def is_present(self) -> bool:
        """Return whether an object is present."""
        return self.value() < self._simple_threshold


class AGCDetector(Detector):
    """A threshold detector with automatic gain control."""

    def __init__(self, detector: Detector, base_threshold=10, gain: float = 1.0) -> None:
        """Initialise a detector with AGC."""
        self.value = detector.value
        self.base = self.value()
        self.base_threshold = base_threshold
        self.gain = gain

        self.last_time = utime.ticks_ms()

    def is_present(self) -> bool:
        """
        Apply gain to the detector value and return whether an object is present.

        AGC is only applied when an object is absent.

        Returns True if an object is present, False otherwise.
        """
        value = self.value()
        if value < self.base - self.base_threshold:
            return True
        else:
            time = utime.ticks_ms()
            time_delta = utime.ticks_diff(time, self.last_time) / 1000  # seconds
            value_delta = value - self.base
            self.base = self.base + value_delta * self.gain * time_delta
            self.last_time = time

            return False


class SchmittDetector(AnalogueDetector):
    """A detector with Schmitt trigger functionality."""

    DEFAULT_THRESHOLD = 2**10 / 2  # mid-point of 10-bit ADC

    def __init__(
        self,
        detector: Detector,
        trigger_threshold=DEFAULT_THRESHOLD,
        release_threshold=DEFAULT_THRESHOLD,
    ) -> None:
        """Initialise a Schmitt trigger detector."""
        self.value = detector.value
        self.trigger_threshold = trigger_threshold
        self.release_threshold = release_threshold

        self._next_trigger = 0
        self._cleared = True

    def is_present(self, time_hysteresis=0) -> int:
        """
        Monitor the detector using a Schmitt trigger.

        Acts as a set-reset flip-flop with time and value hysteresis.
        Returns TRIGGER on rising edge, RELEASE on falling edge, and NONE otherwise.
        """
        value = self.value()
        is_ready = self._next_trigger <= utime.ticks_ms() and self._cleared

        if value < self.trigger_threshold and is_ready:
            self._next_trigger = utime.ticks_add(utime.ticks_ms(), time_hysteresis)
            self._cleared = False
            return DetectorEvent.TRIGGER
        elif value > self.release_threshold and not self._cleared:
            self._cleared = True
            return DetectorEvent.RELEASE

        return DetectorEvent.NONE


if __name__ == "__main__":
    led = Pin("LED", Pin.OUT)
    detector = AnalogueDetector(28, simple_threshold=150)

    def bar(value: int) -> str:
        """Return unicode blocks representing the value between 0 and 255."""
        return "_" if value < 56 else "O"

    while True:
        is_present = detector.is_present()
        value = detector.value()

        led.value(is_present)

        print(f"{' ' * (value // 4)}{'X' if is_present else '|'} {value}{' ' * 10}", end="\r")
        # print(bar(value), end="")

        utime.sleep_ms(30)
