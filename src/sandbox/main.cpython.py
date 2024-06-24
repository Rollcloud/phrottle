import json
import time

from microdot import Microdot, send_file
from microdot_websocket import with_websocket

try:
    import hardware
except Exception:
    # in normal python
    import mock_hardware as hardware

import throttle
from layout import RelativeDirection

ONE_HOUR_IN_SECONDS = 60 * 60
ONE_DAY_IN_SECONDS = ONE_HOUR_IN_SECONDS * 24

flash_led = hardware.flash_led

flash_led(n=2)  # show that wifi connection was successful


app = Microdot()


def title(string: str):
    return string[0].upper() + string[1:]


@app.before_request
def before(request):
    flash_led(t=0.01)


@app.get("/favicon.ico")
def favicon(request):
    return send_file("src/static/favicon.ico", max_age=ONE_HOUR_IN_SECONDS)


@app.route("/static/<path:path>")
def static(request, path):
    if ".." in path:
        # directory traversal is not allowed
        return "Not found", 404
    return send_file("src/static/" + path, max_age=ONE_DAY_IN_SECONDS)


@app.get("/")
def index(request):
    return send_file("src/templates/throttle.html")


@app.route("/move")
@with_websocket
def echo(request, ws):
    while True:
        incoming = ws.receive()
        print(incoming)
        message = json.loads(incoming)
        if message["type"] == "ping":
            reply = {"type": "pong", "date": time.time()}
            ws.send(json.dumps(reply))
        else:
            # echo message
            reply = message

        ws.send(json.dumps(reply))


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


@app.get("/shutdown")
def shutdown(request):
    request.app.shutdown()
    return "The server is shutting down..."


try:
    address = "localhost"
    print(f"Running app on http://{address}")
    app.run(port=80, debug=True)
except Exception as err:
    flash_led(t=1, n=5)
    import sys

    sys.print_exception(err)
