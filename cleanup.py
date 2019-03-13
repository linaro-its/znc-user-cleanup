#!/usr/bin/python3
#

import os
import json
from json_minify import json_minify
import socket
import ssl
import atexit
import distutils
import time


class Irc:
    def __init__(self, port, use_ssl):
        non_ssl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if use_ssl:
            # Wrap SSL around the socket. We try to be as permissive as
            # possible as that will then allow the server to be as
            # restrictive as it likes, e.g. TLSv1.2 only.
            self.socket = ssl.wrap_socket(
                non_ssl,
                ssl_version=ssl.PROTOCOL_SSLv23
            )
        else:
            self.socket = non_ssl
        self.socket.connect(("localhost"), port)
        atexit.register(self.cleanup)

    def cleanup(self):
        self.socket.close()

    def send(self, msg):
        # Make the socket blocking so we can use sendall
        self.socket.setblocking(1)
        self.socket.sendall(msg.encode())

    def receive(self, timeout=2):
        # Make the socket non-blocking
        self.socket.setblocking(0)
        # Total data partwise in an array
        total_data = []
        data = ''
        # Beginning time
        begin = time.time()
        while 1:
            # If you got some data then break after timeout
            if total_data and time.time()-begin > timeout:
                break
            # If you got no data at all, wait a little longer, twice the
            # timeout
            elif time.time()-begin > timeout*2:
                break
            # Receive something
            try:
                data = self.socket.recv(8192)
                if data:
                    total_data.append(data.decode())
                    # Change the beginning time for measurement
                    begin = time.time()
                else:
                    # Sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except Exception:
                pass
        # Join all parts to make final string
        return ''.join(total_data)

    def logon(self, username, password):
        self.send("NICK %s\r\n" % username)
        self.send("PASS %s:%s\r\n" % (username, password))
        self.send("USER %s 0 * :%s\r\n" % (username, username))
        self.receive()

    def get_users(self):
        # Get a list of users from the server
        users = []
        self.send("PRIVMSG *controlpanel :ListUsers\r\n")
        results = self.receive()
        lines = results.split("\r\n")
        for line in lines:
            parts = line.split(" ")
            if len(parts) > 4:
                users.append(parts[4])
        return users


def main():
    # Read the configuration file
    basedir = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(basedir, "configuration.jsonc")) as f:
        configuration = json.loads(json_minify(f.read()))
    if "port" in configuration:
        port = int(configuration["port"])
    else:
        raise ValueError("'port' missing from configuration file")
    if "ssl" in configuration:
        use_ssl = bool(distutils.util.strtobool(
            configuration["ssl"]
        ))
    else:
        raise ValueError("'ssl' missing from configuration file")
    irc = Irc(port, use_ssl)
    users = irc.get_users()
    print(users)


if __name__ == '__main__':
    main()
