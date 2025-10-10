"""Create host WiFi network."""

from hardware import LED, PWM_LED, WiFi

wifi = None
wifi_led = None
speed_led = None

if __name__ == "__main__":
    wifi_led = LED()
    speed_led = PWM_LED(16)

    wifi = WiFi()
    wifi_led.pin.on()
    wifi.share_access_point()
    wifi_led.pin.off()
    wifi.open_connection()
    wifi_led.pin.on()

    wifi.send("HELLO", wifi.broadcast)

    while True:
        data = wifi.receive(include_ip_address=True)

        if not data:
            continue

        message, ip_address = data

        if b"MARCO" in message:
            wifi.send("POLO", ip_address)
        elif b"CONTROL" in message:
            wifi.send("ECHO " + message.decode(), wifi.broadcast)
            _control, direction, speed = message.split()

            if direction == b"R":
                speed_led.on()
            elif direction == b"F":
                speed_led.off()

            speed_led.brightness(int(speed))
