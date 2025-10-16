import random
import socket
import time

import network
from machine import ADC, PWM, Pin
from simply_robotics import CorelessMotor  # noqa: F401


class Switch:
    """An ON-OFF input switch with an internal pull-up resistor."""

    def __init__(self, gpio, pull=Pin.PULL_UP) -> None:
        self.pin = Pin(gpio, Pin.IN, pull)

    def is_high(self) -> int:
        return 1 - self.pin.value()  # invert the value for pull-up resistor


class Slider:
    """An analogue percentage detector."""

    def __init__(self, gpio) -> None:
        self.adc = ADC(Pin(gpio, Pin.IN))

    def value(self):
        """Return the value as an integer between 0 and 128."""
        value = self.adc.read_u16() >> 9

        return max(0, min(value - 14, 100))  # centralise and limit returned result


class LED:
    """A simple LED."""

    def __init__(self, gpio="LED", enable_pwm=False):
        self.pin = Pin(gpio, Pin.OUT)


class PWM_LED:
    """A brightness-changing LED."""

    def __init__(self, gpio):
        self.pin = Pin(gpio, Pin.OUT)
        self.pwm = PWM(self.pin)
        self.pwm.freq(1000)

        self.active = True
        self.value = 0

    def brightness(self, value: int):
        """Set the brightness of the LED, if it is active, by providing a number between 0 and 100."""
        if self.active:
            self.value = max(0, min(value, 100))
            self.pwm.duty_u16(int(self.value / 100 * 65535))

    def activate(self):
        self.active = True

    def off(self):
        """Deactivate the LED."""
        self.active = False
        self.pwm.duty_u16(0)

    def on(self):
        """Activate the LED."""
        self.active = True
        self.pwm.duty_u16(65535)


class Indicator:
    """A visual element that can appear in different guises, coupled with advanced effects."""

    MAX_PWM = 65535

    # Base ranges for guises
    OFF = ((0, 0, 0), (0, 0, 0))
    ORANGE = ((1, 0.2, 0), (1, 0.8, 0))
    BLUE = ((0, 0, 1), (0.2, 0.2, 1))
    PURPLE = ((0.7, 0, 0.7), (1, 0, 1))

    def __init__(self, red_gpio, green_gpio, blue_gpio) -> None:
        self.red_pin = Pin(red_gpio, Pin.OUT)
        self.green_pin = Pin(green_gpio, Pin.OUT)
        self.blue_pin = Pin(blue_gpio, Pin.OUT)

        self.red_pwm = PWM(self.red_pin)
        self.green_pwm = PWM(self.green_pin)
        self.blue_pwm = PWM(self.blue_pin)

        self.red_pwm.freq(1024)
        self.green_pwm.freq(1024)
        self.blue_pwm.freq(1024)

        self.guise = self.OFF

    def pwm_led(self, red: int, green: int, blue: int):
        """Set the led to the given PWM values out of 65535."""
        # invert the values for common anode
        self.red_pwm.duty_u16(self.MAX_PWM - red)
        self.green_pwm.duty_u16(self.MAX_PWM - green)
        self.blue_pwm.duty_u16(self.MAX_PWM - blue)

    def show_guise(self, guise, effect=None):
        if effect == "flicker":
            probability_change = random.random()
            if probability_change >= 0.005:
                return

        ((red_low, green_low, blue_low), (red_high, green_high, blue_high)) = guise

        red_value = random.randint(int(red_low * self.MAX_PWM), int(red_high * self.MAX_PWM))
        green_value = random.randint(int(green_low * self.MAX_PWM), int(green_high * self.MAX_PWM))
        blue_value = random.randint(int(blue_low * self.MAX_PWM), int(blue_high * self.MAX_PWM))

        self.pwm_led(red_value, green_value, blue_value)

    def toggle(self, guise_1, guise_2):
        if self.guise == guise_1:
            self.show_guise(guise_2)
        else:
            self.show_guise(guise_1)


class WiFi:
    """Connection to WiFi."""

    ssid = "Guard"
    password = "ebbandflow"
    broadcast = "255.255.255.255"
    host = "0.0.0.0"
    port = 50007  # arbitrary non-privileged port

    def share_access_point(self):
        wlan = network.WLAN(network.AP_IF)
        wlan.config(essid=self.ssid, password=self.password)
        wlan.active(True)

        while wlan.active() is False:
            pass

        self.wlan = wlan
        status = wlan.ifconfig()
        self.ip_address = status[0]

    def connect_to_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.ssid, self.password)

        # Wait for connect or fail
        max_wait = 10
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            time.sleep(1)

        # Handle connection error
        if wlan.status() != 3:
            raise RuntimeError("network connection failed")
        else:
            # success
            self.wlan = wlan
            status = wlan.ifconfig()
            self.ip_address = status[0]

            return True

    def disconnect_wifi(self):
        """Completely deactivate the WiFi interface."""
        self.wlan.disconnect()
        self.wlan.active(False)
        self.wlan.deinit()
        self.ip_address = None

    def open_udp_socket(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Reuse socket
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Enable broadcasting mode
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        client.settimeout(0.1)

        # Bind socket to port
        addr = socket.getaddrinfo(self.host, self.port, socket.AF_INET, socket.SOCK_DGRAM)[0][-1]
        client.bind(addr)

        self.client = client

    def close_udp_socket(self):
        try:
            self.client.close()
        except Exception:
            pass  # ignore all exceptions, we just want to close

    def send(self, message, ip_address=None):
        if ip_address is None:
            ip_address = self.server_ip_address

        address = socket.getaddrinfo(
            ip_address,
            self.port,
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )[0][-1]
        self.client.sendto(message.encode(), address)

    def send_marco(self):
        self.send("MARCO", ip_address=self.broadcast)
        time.sleep(0.3)

    def receive(self, include_ip_address=False):
        try:
            data, (ip_address, _port) = self.client.recvfrom(1024)
        except OSError:  # OSError: [Errno 110] ETIMEDOUT
            # To be expected if no message has been received
            return None

        if include_ip_address:
            return data, ip_address

        return data

    def receive_polo(self):
        data = self.receive(include_ip_address=True)

        if data is None:
            return

        message, ip_address = data

        if "POLO" in message:
            self.server_ip_address = ip_address

            return True
