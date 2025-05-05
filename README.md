# ![lever-arm](src/static/lever-arm.png) Phrottle

A model railway throttle for the Pico.

## Requirements

- Pico W
- Kitronic Simply Robotics Motor Driver Board
- Power Supply (12V maximum)
- Locomotive (or any 12V motor)

## Installation

### Dev Setup

1. Install Poetry

1. Setup Poetry

1. Run Ruff

   ```sh
   python -m ruff check --fix
   ```

1. Run PyTest
   ```sh
   python -m pytest
   ```

### Pico Setup

With thanks to [SoongJr](https://github.com/SoongJr/pi-pico/blob/main/README.md) for the WiFi configuration and depedency installation scripts and instructions.

1. Flash micropython onto your pico (you can get [the latest build](https://micropython.org/download/RPI_PICO_W/))
1. Transfer and run `setup/configure-wifi.py` on the pico (after which you have to hit Ctrl+X to get out of REPL)
   ```sh
   rshell 'cp setup/configure-wifi.py /pyboard; repl ~ exec(open("/configure-wifi.py").read())'
   ```
   This will prompt for credentials and write them into a file on the pico, so there is no chance you'll accidentally upload them to github.
1. Run `python .\src\setup\sync.py` to transfer all files from `src/rp2` to the pico board

## Run

Use the Pico Device Controller to run `main.py`, `server.py`, or one of the sandbox scripts.

## Libraries

The external library `umqtt.simple` is required to be loaded onto the Pico for data-logging work.

```sh
mpremote mip install umqtt.simple
```

If a typing import error such as `ImportError: no module named 'typing'`,
then install a mock typing module such as https://micropython-stubs.readthedocs.io/en/main/typing_mpy.html#install-the-typing-modules-to-your-mcu

```sh
mpremote mip install github:josverl/micropython-stubs/mip/typing.mpy
```

## Attributions

- Lever Icon: [Gambling icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/gambling)
