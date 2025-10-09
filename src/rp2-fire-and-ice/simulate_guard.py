# Simulate the Guard semi-automatic driver
"""
Simple udp socket server.

sources:
 - https://docs.python.org/3/library/socket.html#example
 - https://gist.github.com/ninedraft/7c47282f8b53ac015c1e326fffb664b5
"""

import socket

HOST = ""  # Symbolic name meaning all available interfaces
PORT = 50007  # Arbitrary non-privileged port
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as server:
    # Enable port reusage so we will be able to run multiple clients and servers on single (host, port).
    # Do not use socket.SO_REUSEADDR except you using linux(kernel<3.9): goto https://stackoverflow.com/questions/14388706/how-do-so-reuseaddr-and-so-reuseport-differ for more information.
    # For linux hosts all sockets that want to share the same address and port combination must belong to processes that share the same effective user ID!
    # So, on linux(kernel>=3.9) you have to run multiple servers and clients under one user to share the same (host, port).
    # Thanks to @stevenreddie
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Set a timeout so the socket does not block
    # indefinitely when trying to receive data.
    server.settimeout(0.1)

    server.bind((HOST, PORT))

    while True:
        try:
            message, (ip_address, _port) = server.recvfrom(1024)
            print(f"Rx [{ip_address}] {message}")

            if b"ECHO" in message:
                pass
            elif b"MARCO" in message:
                server.sendto(b"POLO", (ip_address, PORT))
                print(f"Tx [{ip_address}] {b'POLO'}")
            else:
                message = b"ECHO " + message
                server.sendto(message, (ip_address, PORT))
                print(f"Tx [{ip_address}] {message}")

        except TimeoutError:
            pass  # this is to be expected if no message has been received
