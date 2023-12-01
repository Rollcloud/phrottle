import json
import os
import time

import mip
import network

# read WIFI configuration from file system
with open("/.wifi/connections.json", "r", encoding="utf-8") as f:
    connections = json.load(f)
# connect
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(connections[0]["ssid"], connections[0]["password"])
# Wait for connect or fail
while True:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    print("waiting for connection...")
    time.sleep(1)
# Handle connection error
if wlan.status() != 3:
    raise RuntimeError("network connection failed")
else:
    print("connected to wifi " + connections[0]["ssid"])
print()


def list_members(classname):
    print(
        str(classname)
        + " contains: "
        + ", ".join(i for i in sorted(dir(classname)) if not i.startswith("_"))
    )


def print_free_size():
    f_frsize, f_bfree = (os.statvfs("/")[1], os.statvfs("/")[3])
    print("free size in flash: {}kB".format((f_bfree * f_frsize) / 1024))


def verify_phew():
    # verify it can be imported and list exposed classes
    print(
        "/lib/phew contains: " + ", ".join(i for i in sorted(os.listdir("/lib/phew")))
    )
    import phew
    from phew import connect_to_wifi, server

    list_members(phew)
    list_members(phew.server)


print_free_size()
print()
# (re)install phew, then verify it can be loaded
# mip.install("micropython-phew")
mip.install("github:pimoroni/phew")
verify_phew()
print()
print_free_size()
