from phew import get_ip_address, server
from phew.logging import LOG_ALL, disable_logging_types
from phew.template import render_template

from layout import RelativeDirection
import hardware
import wifi
import throttle

disable_logging_types(LOG_ALL)
flash_led = hardware.flash_led

wifi.connect()
flash_led(n=2)  # show that wifi connection was successful


def title(string: str):
    return string[0].upper() + string[1:]


@server.route("/favicon.ico", methods=["GET"])
def favicon(request):
    pass


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

    direction = RelativeDirection.FORWARD if dir == "forward" else RelativeDirection.REVERSE
    throttle.move(direction)
    return render_template(
        "templates/jumbotron-page.html",
        title=f"Moving {title(dir)}",
        heading=f"Move {title(dir)}",
    )


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
