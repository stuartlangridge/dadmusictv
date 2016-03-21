#!/usr/bin/env python

# Ensure that only one of these is running, otherwise they'll both add songs to the playlist.
# Linux-specific, but that's fine.
try:
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    # Create an abstract socket, by prefixing it with null
    s.bind("\0dadmusictv_shuffler")
except socket.error, e:
    print "An instance of this shuffler is already running. Aborting."
    import sys
    sys.exit(0)

import random
from mpd import MPDClient
client = MPDClient()
while 1:
    try:
        client.connect('localhost',6600)
        break
    except:
        print "Couldn't connect to music; waiting a bit and trying again"
        time.sleep(5)

# Read the whole library. Not a problem, because dadmusictv expects you
# to restart the Pi if you've added new songs anyway.
songs = [x["file"] for x in client.listall() if x.has_key("file")]

while 1:
    client.idle()
    s = client.status()
    if s.get("state") == "play" and s.get("nextsong") is None:
        # We are at the end of the playlist. Remove all previous songs...
        while len(client.playlistinfo()) > 2:
            client.delete(0)
        # ...and add a random song
        client.add(random.choice(songs))
