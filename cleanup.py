#!/usr/bin/python3
#
# This script compares the list of ZNC user accounts with the user directories
# and, depending on the config settings, either deletes or moves to a trash
# folder those directories that no longer belong to active accounts.
#
# Copyright 2019 Philip Colmer, Linaro Ltd

import os
import json
from json_minify import json_minify
import socket
import ssl
import atexit
import distutils
import time
import shutil


class Irc:
    def __init__(self, port, use_ssl, show_comms):
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
        self.socket.connect(("localhost", port))
        self.show_comms = show_comms
        atexit.register(self.cleanup)

    def cleanup(self):
        self.socket.close()

    def send(self, msg):
        # Make the socket blocking so we can use sendall
        if self.show_comms:
            print("Sending: %s" % msg)
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
        result = ''.join(total_data)
        if self.show_comms:
            print("Received: %s" % result)
        return result

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
        # Sanity check that what we've received looks like we've
        # correctly interpreted the output from ListUsers.
        if len(users) == 0 or users[0] != "Username":
            raise ValueError((
                "Response from 'ListUsers' command has not met expectations."
                " Please check connection configuration, particularly port"
                " and ssl. If they look correct, change 'debug' to True to"
                " make sure that ListUsers is working and the output"
                " is as expected."
            ))
        return users


def process_directory(userdir, configpath, trashpath):
    if trashpath == "":
        print("Deleting %s" % userdir)
        shutil.rmtree("%s/users/%s" % (configpath, userdir))
    else:
        print("Moving %s to trash dir" % userdir)
        shutil.move(
            "%s/users/%s" % (configpath, userdir),
            trashpath
        )


def check_users(configpath, trashpath, users):
    # Check all of the user directories underneath the config path.
    # If there are any directories that aren't in the users list,
    # action them according to the setting of trashpath.
    dirs = next(os.walk("%s/users" % configpath))[1]
    for dir in dirs:
        if dir not in users:
            process_directory(dir, configpath, trashpath)


def main():
    # Read the configuration file
    basedir = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(basedir, "config.jsonc")) as f:
        configuration = json.loads(json_minify(f.read()))
    if "debug" in configuration:
        show_comms = bool(distutils.util.strtobool(
            configuration["debug"]
        ))
    else:
        show_comms = False
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
    if "adminnick" in configuration:
        user = configuration["adminnick"]
        if user == "":
            raise ValueError("'adminnick' hasn't been set")
    else:
        raise ValueError("'adminnick' missing from configuration file")
    if "adminpw" in configuration:
        password = configuration["adminpw"]
        if password == "":
            raise ValueError("'adminpw' hasn't been set")
    else:
        raise ValueError("'adminpw' missing from configuration file")
    if "zncconfigpath" in configuration:
        zncconfigpath = configuration["zncconfigpath"]
        if zncconfigpath == "":
            raise ValueError("'zncconfigpath' hasn't been set")
        # Make sure the path string does NOT end with /.
        if zncconfigpath[-1] == "/":
            zncconfigpath = zncconfigpath[:-1]
    else:
        raise ValueError("'zncconfigpath' missing from configuration file")
    if "trashpath" in configuration:
        trashpath = configuration["trashpath"]
        if trashpath == "MUSTBEEDITED":
            raise ValueError(
                "'trashpath' has not been reviewed for a correct value")
    else:
        raise ValueError("'trashpath' missing from configuration file")
    irc = Irc(port, use_ssl, show_comms)
    irc.logon(user, password)
    users = irc.get_users()
    check_users(zncconfigpath, trashpath, users)


if __name__ == '__main__':
    main()
