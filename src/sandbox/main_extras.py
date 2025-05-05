import hardware
import throttle
import wifi
from layout import RelativeDirection
from phew import get_ip_address, server
from phew.logging import LOG_ALL, disable_logging_types
from phew.template import render_template

disable_logging_types(LOG_ALL)
flash_led = hardware.flash_led

wifi.connect()
flash_led(n=2)  # show that wifi connection was successful


def title(string: str):
    return string[0].upper() + string[1:]


@server.route("/", methods=["GET"])
def hello(request):
    flash_led(t=0.01)
    return render_template("templates/throttle.html")


@server.route("/world", methods=["GET"])
def world(request):
    flash_led(t=0.01)
    return render_template(
        "templates/jumbotron-page.html",
        title="Hello Wide World",
        heading="Welcome to the",
        sub_heading="World Wide Web",
    )


@server.route("/stop", methods=["GET"])
def stop(request):
    flash_led(t=0.01)

    throttle.stop()
    return render_template(
        "templates/jumbotron-page.html",
        title="Stopping",
        heading="Stopping",
    )


@server.route("/move/<dir>", methods=["GET"])
def move(request, dir):
    flash_led(t=0.01)

    acceptable_dirs = ["forward", "reverse", "left", "right"]

    if dir == "left":
        dir = "forward"
    if dir == "right":
        dir = "reverse"

    if dir not in acceptable_dirs:
        return render_template(
            "templates/jumbotron-page.html",
            title="400 Bad Request",
            heading="400 Bad Request",
            sub_heading=f"Direction '{dir}' is no one of {', '.join(acceptable_dirs)}",
        )

    direction = (
        RelativeDirection.FORWARD if dir == "forward" else RelativeDirection.REVERSE
    )
    throttle.move(direction)
    return render_template(
        "templates/jumbotron-page.html",
        title=f"Moving {title(dir)}",
        heading=f"Move {title(dir)}",
    )


@server.route("/flash/<n>", methods=["GET"])
def _flash(request, n):
    flash_led(n=int(n))
    return f"Flashed {n} times"


@server.route("/temperature", methods=["GET"])
def temperature(request):
    flash_led(t=0.01)
    return render_template(
        "templates/jumbotron-page.html",
        title="Temperature",
        heading=f"{hardware.get_internal_temperature():.1f}°C",
        sub_heading="Internal Temperature",
    )


@server.route("/random", methods=["GET"])
def random_number(request):
    flash_led(t=0.01)
    import random

    min = int(request.query.get("min", 0))
    max = int(request.query.get("max", 100))
    return str(random.randint(min, max))


@server.catchall()
def catchall(request):
    flash_led(t=0.01)
    return render_template(
        "templates/jumbotron-page.html",
        title="404 Not Found",
        heading="404 Not Found",
        sub_heading="This is not the page you're looking for",
    )


try:
    address = get_ip_address()
    print(f"Running server on http://{address}")
    server.run()
except KeyboardInterrupt:
    server.stop()
    server.close()
except Exception as err:
    flash_led(t=1, n=5)
    import sys

    sys.print_exception(err)
