import json
import time

from microdot_asyncio import Microdot, send_file
from microdot_asyncio_websocket import with_websocket

import hardware
import throttle
import wifi
from layout import RelativeDirection

ONE_HOUR_IN_SECONDS = 60 * 60
ONE_DAY_IN_SECONDS = ONE_HOUR_IN_SECONDS * 24

flash_led = hardware.flash_led

address = wifi.connect_with_saved_credentials()
flash_led(n=2)  # show that wifi connection was successful


app = Microdot()


def title(string: str):
    return string[0].upper() + string[1:]


@app.before_request
def before(request):
    flash_led(t=0.01)


@app.get("/favicon.ico")
def favicon(request):
    return send_file("/static/favicon.ico", max_age=ONE_HOUR_IN_SECONDS)


@app.get("/script.js")
def script(request):
    return send_file("script.js")


@app.route("/static/<path:path>")
def static(request, path):
    if ".." in path:
        # directory traversal is not allowed
        return "Not found", 404
    return send_file("static/" + path, max_age=ONE_HOUR_IN_SECONDS)


@app.get("/")
def index(request):
    return send_file("templates/throttle.html")


@app.route("/move")
@with_websocket
async def move_ws(request, ws):
    while True:
        incoming = await ws.receive()
        flash_led(t=0.005)
        message = json.loads(incoming)
        if message["type"] == "ping":
            reply = {"type": "pong", "date": time.time()}
        elif message["type"] == "stop":
            throttle.stop()
            reply = {
                "type": "ack",
                "text": f"commanded: {throttle.velocity()}",
                "date": time.time(),
            }
        elif message["type"] == "move":
            direction_in = message["text"]
            if direction_in == "left":
                direction_in = "forward"
            if direction_in == "right":
                direction_in = "reverse"

            direction = (
                RelativeDirection.FORWARD
                if direction_in == "forward"
                else RelativeDirection.REVERSE
            )

            throttle.accelerate(direction)
            reply = {
                "type": "ack",
                "text": f"commanded: {throttle.velocity()}",
                "date": time.time(),
            }
        else:
            # echo message
            print(message)
            reply = message

        await ws.send(json.dumps(reply))


@app.get("/stop")
def stop(request):
    throttle.stop()
    return "stopping"


@app.get("/move/<dir>")
def move(request, dir):
    acceptable_dirs = ["forward", "reverse", "left", "right"]

    if dir == "left":
        dir = "forward"
    if dir == "right":
        dir = "reverse"

    if dir not in acceptable_dirs:
        return f"Direction '{dir}' is no one of {', '.join(acceptable_dirs)}", 400

    direction = RelativeDirection.FORWARD if dir == "forward" else RelativeDirection.REVERSE
    throttle.move(direction)
    return f"moving {title(dir)}"


@app.errorhandler(404)
def not_found(request):
    return "This is not the page you're looking for", 404


try:
    print(f"Running app on http://{address}")
    app.run(port=80)
except KeyboardInterrupt:
    throttle.stop()
    app.shutdown()
except Exception as err:
    flash_led(t=1, n=5)
    import sys

    sys.print_exception(err)
