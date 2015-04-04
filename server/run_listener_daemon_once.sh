#!/bin/bash

# This is a shell script because when the bluetooth connection drops,
# bluetoothd starts refusing connections. So, we stop and start
# bluetooth, and then run the listener daemon; when the listener daemon
# exits, supervisord will start us again and that'll restart bluetooth,
# and then connections work again.

# Note that stopping and restarting bluetooth requires root, and the
# pi user is set up to have sudo rights without a password; if you
# don't do that then the script will fail because you do not have
# the rights!

sudo -n service bluetooth restart
python /home/pi/dadmusictv/listener_daemon.py

