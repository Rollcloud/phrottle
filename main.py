from phew import get_ip_address, server
from phew.logging import LOG_ALL, disable_logging_types
from phew.template import render_template

import hardware
import wifi

disable_logging_types(LOG_ALL)
flash_led = hardware.flash_led

wifi.connect()
flash_led(n=2)  # show that wifi connection was successful


@server.route("/", methods=["GET"])
def hello(request):
    flash_led(t=0.01)
    return render_template(
        "templates/page.html", title="Hello World", content="Hello World!"
    )


@server.route("/world", methods=["GET"])
def world(request):
    flash_led(t=0.01)
    return render_template(
        "templates/jumbotron-page.html",
        title="Hello Wide World",
        heading="Welcome to the",
        sub_heading="World Wide Web",
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
