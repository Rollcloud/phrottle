"""
A module for handing detectors and their behaviours.

A detector is a sensor that returns a numerical value.
A converter transforms the value into a boolean indicating presence.
A behaviour modifies the converter's presence output.
"""

import utime
from machine import ADC, Pin

DEFAULT_THRESHOLD = 2**10 / 2  # mid-point of 10-bit ADC


class BehaviourEvent:
    """Events that can be triggered by behaviours."""

    NONE = 0
    TRIGGER = 1
    RELEASE = 2


class Detector:
    """A base class for detectors providing common functionality."""

    def value(self) -> int:
        """Return the detector value."""
        raise NotImplementedError


class DigitalDetector(Detector):
    """A detector for a digital sensor."""

    def __init__(self, gpio_number) -> None:
        """Initialise a digital sensor connected to the provided pin."""
        self.gpio_number = gpio_number
        self._sensor = Pin(gpio_number, Pin.IN)

    def value(self) -> int:
        """Return the pin value."""
        return self._sensor.value()


class AnalogueDetector(Detector):
    """A basic detector for an analogue sensor."""

    def __init__(self, gpio_number) -> None:
        """Initialise an analogue sensor detector connected to the provided pin."""
        self.gpio_number = gpio_number
        self._sensor = ADC(gpio_number)

    def value(self) -> int:
        """Return the ADC value in bits."""
        return self._sensor.read_u16() >> 6  # 10-bit ADC


class Converter:
    """A base class for converters providing common functionality."""

    def is_present(self) -> bool:
        """Return whether an object is present."""
        raise NotImplementedError


class SimpleThresholdConverter(Converter):
    """A converter for a simple threshold."""

    def __init__(
        self, detector: Detector, threshold=DEFAULT_THRESHOLD, present_on_high=True
    ) -> None:
        """Initialise a simple threshold converter."""
        self.value = detector.value
        self.threshold = threshold
        self.present_on_high = present_on_high

    def is_present(self) -> bool:
        """
        Return whether an object is present.

        Returns True if the value is above the threshold, False otherwise.
        Output is inverted if present_on_high is False.
        """
        if self.present_on_high:
            return self.value() >= self.threshold
        else:
            return self.value() <= self.threshold


class SchmittConverter(Converter):
    """A Schmitt trigger converter."""

    def __init__(
        self,
        detector: Detector,
        trigger_threshold=DEFAULT_THRESHOLD,
        release_threshold=DEFAULT_THRESHOLD,
    ) -> None:
        """Initialise a Schmitt trigger converter."""
        self.detector = detector
        self.trigger_threshold = trigger_threshold
        self.release_threshold = release_threshold
        self._is_present = False

    def is_present(self) -> bool:
        """Return whether an object is present using a Schmitt trigger."""
        value = self.detector.value()
        if value < self.trigger_threshold:
            self._is_present = True
        elif value > self.release_threshold:
            self._is_present = False

        return self._is_present


class AGCConverter(Converter):
    """A converter with automatic gain control."""

    def __init__(self, detector: Detector, base_threshold=10, gain: float = 1.0) -> None:
        """Initialise a converter with AGC."""
        self.detector = detector
        self.base = self.detector.value()
        self.base_threshold = base_threshold
        self.gain = gain

        self._last_time = utime.ticks_ms()

    def is_present(self) -> bool:
        """
        Apply gain to the detector value and return whether an object is present.

        AGC is only applied when an object is absent.

        Returns True if an object is present, False otherwise.
        """
        value = self.detector.value()
        if value < self.base - self.base_threshold:
            return True
        else:
            time = utime.ticks_ms()
            time_delta = utime.ticks_diff(time, self._last_time) / 1000  # seconds
            value_delta = value - self.base
            self.base = self.base + value_delta * self.gain * time_delta
            self._last_time = time

            return False


class Behaviour:
    """A base class for behaviours providing common functionality."""

    def is_present(self) -> bool:
        """Return whether an object is present."""
        raise NotImplementedError


class DebounceBehaviour(Behaviour):
    """
    Apply a time-based debounce to a detector.

    Will prevent multiple triggers within the debounce time.
    """

    def __init__(self, parent_behaviour: Behaviour | Converter, debounce_time_ms=50) -> None:
        """Initialise a debounced behaviour."""
        self.parent_behaviour = parent_behaviour
        self.debounce_time_ms = debounce_time_ms
        self._present_until = utime.ticks_ms()

    def is_present(self):
        """Return whether an object is present, staying present for the debounce time."""
        time = utime.ticks_ms()
        stay_present = time < self._present_until
        is_present = self.parent_behaviour.is_present()

        if stay_present:
            return True
        elif is_present:
            self._present_until = utime.ticks_add(time, self.debounce_time_ms)
            return True
        else:
            return False


class EventOnChangeBehaviour(Behaviour):
    """Trigger an event when the presence state changes."""

    def __init__(self, parent_behaviour: Behaviour | Converter) -> None:
        """Initialise an event-on-change behaviour."""
        self.parent_behaviour = parent_behaviour
        self._last_present = False

    def check_event(self) -> int:
        """Check for an event."""
        is_present = self.parent_behaviour.is_present()
        event = BehaviourEvent.NONE
        if is_present != self._last_present:
            event = BehaviourEvent.TRIGGER if is_present else BehaviourEvent.RELEASE
            self._last_present = is_present

        return event


if __name__ == "__main__":
    led = Pin("LED", Pin.OUT)
    # detector = TouchDetector(0)
    detector = AnalogueDetector(28, simple_threshold=150)

    while True:
        is_present = detector.is_present()
        value = detector.value()

        led.value(is_present)

        print(f"{' ' * (value // 4)}{'X' if is_present else '|'} {value}{' ' * 10}", end="\r")

        utime.sleep_ms(30)
