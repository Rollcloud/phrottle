import json

from definitions import point
from hardware import get_internal_temperature
from umqtt.simple import MQTTClient

MQTT_BROKER = "192.168.88.117"

# Set up the script

is_running = False
stop_when = (-1, 0)


def init_mqtt():
    global qt, MQTT_BROKER
    qt = MQTTClient("pico", MQTT_BROKER, keepalive=300)


def send_sensor_data(timestamps, sensor_data):
    global qt
    num_samples = len(timestamps)
    try:
        qt.connect()
        for timestamp, data in zip(timestamps, sensor_data):
            payload = {
                "timestamp": timestamp,
                "temperature": get_internal_temperature(),
            }
            payload.update(data)
            qt.publish(b"paper_wifi/test/phrottle", json.dumps(payload))
        qt.disconnect()
        timestamps = []
        sensor_data = []
        print(f"Sent {num_samples} samples")
    except OSError as e:
        if e.args[0] == 103:
            # connection aborted, server most not available
            timestamps = []
            sensor_data = []
        else:
            raise e


def getBlockEntrySensor(connections, block_number: int, is_moving_left: bool) -> str:
    """Get the sensor key for sensor that will be triggered when the block is entered."""
    connection_index = 0 if is_moving_left else 1
    for key, block_numbers in connections.items():
        if block_numbers[connection_index] == block_number:
            return key

    available_connections = ", ".join(
        map(
            str,
            sorted({connection[connection_index] for connection in connections.values()}),
        )
    )
    message = (
        "Block number {number} not found in connections\n"
        "Choose from block numbers: [{options}]\n"
        "Or check locomotive direction"
    )
    raise ValueError(
        message.format(
            number=block_number,
            options=available_connections,
        )
    )


def move_wagon(
    blocks, connections, sensor_key: str, is_triggered: bool, is_moving_left: bool
) -> None:
    """Move a wagon based on the sensor key and trigger state."""
    if is_triggered:
        block_number = connections[sensor_key][0 if is_moving_left else 1]
        blocks[block_number] += 1
    else:
        # is released
        block_number = connections[sensor_key][1 if is_moving_left else 0]
        blocks[block_number] -= 1
    return blocks


def check_and_change_point(blocks, sensors, diverge=False, toggle=False):
    """Check if there are any wagons on the point and change the point."""
    if (
        blocks[1] > 0
        or sensors["POINT_BASE_P"].is_present()
        or sensors["POINT_THROUGH_P"].is_present()
        or sensors["POINT_DIVERGE_P"].is_present()
    ):
        print("Wagon present, cannot toggle point.")
    else:
        if toggle:
            print("Toggling point")
            point.toggle()
        else:
            print("Changing point to", "diverge" if diverge else "through")
            point.change(diverge)


def display(sensors, blocks):
    """Show a small diagram of sensor states in the console."""
    hide_cursor = "\033[?25l"
    show_cursor = "\033[?25h"
    start_of_previous_line = "\033[F"
    red = "\033[91m"
    reset = "\033[0m"

    sensor_replacements = {
        "A": "EOT_P",
        "B": "POINT_BASE_P",
        "C": "POINT_THROUGH_P",
        "D": "POINT_DIVERGE_P",
    }

    # fmt: off
    track_diagram = (
        "            /C--2--\n"
        "  |A--0--B=1       \n"
        "            \D--3--\n"
    )
    # fmt: on

    block_replacements = [
        red + str(abs(block)) + reset if block < 0 else str(block) for block in blocks
    ]
    # replace digits with {digits} to avoid replacing the same number twice
    track_diagram_format = "".join(
        f"{{{char}}}" if char.isdigit() else char for char in track_diagram
    )

    track_diagram = track_diagram_format.format(*block_replacements)

    for key, sensor_key in sensor_replacements.items():
        track_diagram = track_diagram.replace(key, "!" if sensors[sensor_key].is_present() else ":")

    return "".join(
        [
            hide_cursor,
            track_diagram,
            start_of_previous_line * 3,
            show_cursor,
        ]
    )
