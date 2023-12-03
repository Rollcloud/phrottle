from microdot import Microdot, send_file
from phew import get_ip_address
from phew.logging import LOG_ALL, disable_logging_types

import hardware
import throttle
import wifi
from layout import RelativeDirection

ONE_HOUR_IN_SECONDS = 60 * 60
ONE_DAY_IN_SECONDS = ONE_HOUR_IN_SECONDS * 24

disable_logging_types(LOG_ALL)
flash_led = hardware.flash_led

wifi.connect()
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


@app.route("/static/<path:path>")
def static(request, path):
    if ".." in path:
        # directory traversal is not allowed
        return "Not found", 404
    return send_file("static/" + path, max_age=ONE_DAY_IN_SECONDS)


@app.get("/")
def index(request):
    return send_file("templates/throttle.html")


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
    address = get_ip_address()
    print(f"Running app on http://{address}")
    app.run(port=80)
except KeyboardInterrupt:
    app.shutdown()
except Exception as err:
    flash_led(t=1, n=5)
    import sys

    sys.print_exception(err)
