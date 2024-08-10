# transfer WIFI credentials to pico board and store them in a file.
# the program can then read this file to connect to WIFI without having to hardcode the credentials and potentially upload them to gitHub.
import errno
import json
import os

connections = [{"ssid": input("SSID: "), "password": input("password: ")}]
parentDir = "/.wifi"
wifiConfigFile = parentDir + "/connections.json"

# create parent directory first:
try:
    os.mkdir(parentDir)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise
# write into file:
with open(wifiConfigFile, "w", encoding="utf-8") as f:
    json.dump(connections, f)
print("successfully written credentials to file system.")
