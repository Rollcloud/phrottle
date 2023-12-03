# ![lever-arm](src/static/lever-arm.png) Phrottle

A model railway throttle for the Pico.

## Requirements

- Pico W
- Kitronic Simply Robotics Motor Driver Board
- Power Supply (12V maximum)
- Locomotive (or any 12V motor)

## Installation

With thanks to [SoongJr](https://github.com/SoongJr/pi-pico/blob/main/README.md) for the WiFi configuration and depedency installation scripts and instructions.

1. Flash micropython onto your pico (you can get [the latest build](https://micropython.org/download/RPI_PICO_W/))
1. Transfer and run `setup/configure-wifi.py` on the pico (after which you have to hit Ctrl+X to get out of REPL)
   ```sh
   rshell 'cp setup/configure-wifi.py /pyboard; repl ~ exec(open("/configure-wifi.py").read())'
   ```
   This will prompt for credentials and write them into a file on the pico, so there is no chance you'll accidentally upload them to github.
1. Run `setup/install-dependencies.py` on the pico, this uses your wifi to install the phew! module:
   ```sh
   rshell 'cp setup/install-dependencies.py /pyboard; repl ~ exec(open("/install-dependencies.py").read())'
   ```

Attributions:

- Lever Icon: [Gambling icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/gambling)
