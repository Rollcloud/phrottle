import _thread
import random
import time

from machine import PWM, Pin

# Define LED pins (adjust pins as needed)
RED_PIN = 13
GREEN_PIN = 15

# Setup LEDs as PWM for flicker control
red_led = PWM(Pin(RED_PIN))
green_led = PWM(Pin(GREEN_PIN))

# PWM frequency - typical for LED flicker control
red_led.freq(1000)
green_led.freq(1000)

# Shared variable to track which LED is currently on: "red" or "green"
current_led = "red"
lock = _thread.allocate_lock()


def flicker_led():
    while True:
        lock.acquire()
        led = current_led
        lock.release()
        if led == "red":
            # Random flicker brightness for red LED, off green LED
            red_led.duty_u16(random.randint(30000, 65000))
            green_led.duty_u16(0)
        elif led == "green":
            # Random flicker brightness for green LED, off red LED
            green_led.duty_u16(random.randint(30000, 65000))
            red_led.duty_u16(0)
        else:
            red_led.duty_u16(0)
            green_led.duty_u16(0)
            break
        # Short random delay for flicker effect
        time.sleep(random.uniform(0.01, 0.1))


def led_alternate():
    global current_led

    try:
        while True:
            with lock:
                current_led = "red"
            time.sleep(2)
            with lock:
                current_led = "green"
            time.sleep(2)
    except KeyboardInterrupt:
        with lock:
            current_led = "none"


# Start flicker thread
_thread.start_new_thread(flicker_led, ())

# Run alternating LED control in main thread
led_alternate()
