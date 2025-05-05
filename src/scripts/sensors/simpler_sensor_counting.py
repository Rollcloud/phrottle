from typing import List

import utime
from machine import ADC

thresholds = [
    # (detect, clear)
    (45, 160),  # 26
    (45, 160),  # 28
]

detected = [False, False]


def init_sensors(pins: List[int]) -> None:
    """Initialise the sensors."""
    return [ADC(gpio_number) for gpio_number in pins]


def read_sensors(sensors: List[ADC]) -> List[int]:
    """Read and return the sensor values."""
    # 10-bit ADC
    return [sensor.read_u16() >> 6 for sensor in sensors]


if __name__ == "__main__":
    sensors = init_sensors([26, 28])

    while True:
        values = read_sensors(sensors)
        for i, (detect, clear) in enumerate(thresholds):
            if values[i] <= detect and not detected[i]:
                detected[i] = True
            elif values[i] >= clear and detected[i]:
                detected[i] = False

        print(values)
        # Print <box-top> if first detected, <box-bottom> if second detected, and <box-full> if both detected, else <box-empty>
        utime.sleep_ms(100)
