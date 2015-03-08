Dad Music TV
------------

Use a Raspberry Pi connected to a TV to play music, with that music stored on the SD card, the player controlled by Bluetooth from an Android phone, and no network at all required once it's running.

Installation
============

(note: these are not newbie instructions. there are no warnings here about "don't overwrite your hard drive". This is almost entirely written just for me; caveat lector.)

Your Raspi will need bluetooth. I have a Bluetooth USB widget, which is a tiny thing and reports itself to lsusb as "bluetooth ID 0a12:0001 Cambridge Silicon Radio, Ltd Bluetooth Dongle (HCI mode)".

1. Download raspbian from http://www.raspberrypi.org/downloads/.
2. unzip the zip file, giving you wheezy-raspbian.img or similar.
3. dd it to the SD card as per http://www.raspberrypi.org/documentation/installation/installing-images/linux.md.
4. unplug sd card. plug it back in.
5. (copy some stuff to the sd card)
6. eject sd card. put it in raspberry pi. plug in raspberry pi. wait for it to show up on the network.
7. ssh pi@raspberrypi.home, password raspberry.
8. As the motd says, run "sudo raspi-config", and expand the filesystem. Finish, and reboot as suggested. ssh in again.
9. sudo apt-get update. sudo apt-get upgrade.
sudo apt-get install python-bluez bluez python-gobject
edit /etc/bluetooth/main.conf and add 
DisablePlugins = pnat
then restart bluetooth with `sudo invoke-rc.d bluetooth restart`
as per http://stackoverflow.com/questions/14618277/rfcomm-without-pairing-using-pybluez-on-debian
confirm you have a bluetooth device with "hciconfig" which should show something.

pair your android phone with the pi:
android: open bluetooth settings and make visible (is visible while settings are open, in Android 5.0+)
pi$ hcitool scan
See your Android phone in the list
pi$ sudo bluez-simple-agent hci0 00:DE:AD:BE:EF:00 # use the address of the Android phone
pi$ enter pin code (e.g., 0000)
android: enter same pin code
devices are now paired

Set up the music stuff:

$ cd
$ ls / > hid
$ sudo mv hid /.hidden
$ sudo mkdir /MUSIC
$ sudo chmod a+rwx /MUSIC

This gives us a folder named MUSIC in the root of the SD card, and ensures that the other folders on the SD card are hidden from the file manager. So when my dad wants to put more music on the card, he can remove it from the Pi, plug it into his computer, and see just a folder named MUSIC into which he drops mp3s.

Put some mp3s in this MUSIC folder, so mpd will have something to look at. Since this is during setup, you can scp some over, or copy them into the SD card if that's easier.

Now we need mpd, which actually does all the music playing etc.

$ sudo apt-get install mpd ncmpcpp

It will likely whine about ipv6 stuff ("mpdlisten: bind to '[::1]:6600' failed") on startup. We do not care because it's only actually going to listen for connections from localhost anyway; the Pi will have no network when it's up and running.

Edit /etc/mpd.conf and set music_directory to be /MUSIC. `sudo service mpd restart` to restart mpd.

We can now use ncmpcpp, the client, to try playing things and see if they worked. Set the output volume to be whatever you want. (Probably 100%; it's not crackly then. You can set the volume that people actually hear stuff at with the volume control on the TV this will eventually be plugged into.)

(here, you need to sod about with making audio go over hdmi. not sure how.)

Now, set up our mpd-over-bluetooth mini-client.



------ end here -------

now to actually set stuff up
$ mkdir recorder
$ cd recorder/
$ sudo apt-get install python-virtualenv python-pip
$ virtualenv --system-site-packages ./venv # need --system-site-packages so it includes pybluez
$ source venv/bin/activate
$ pip install supervisor

Add files supervisor.conf, listener_daemon.py, startup.sh, shutdown.sh, sound_recorder.sh from this repository to /home/pi/recorder.
$ crontab -e
Add a line:
@reboot bash /home/pi/recorder/startup.sh

Reboot the pi. Wait until it starts up. You should now be able to connect, as follows:

open blueterm on android, menu > connect, choose the pi (which will be in the paired list), and you are connected; tap keys on the phone and the pi should show them.

Managing the system
===================

The crontab runs startup.sh on reboot. This starts supervisord, installed from pip. Supervisord starts the listener daemon, which opens a bluetooth serial port and waits for connections. The listener daemon starts and stops the actual sound recorder by using supervisorctl to do so.

To inspect the status of running jobs, first enter the virtualenv and then use supervisorctl status, passing the conf file:

$ cd ~/recorder
$ source venv/bin/activate
$ supervisorctl -c ./supervisor.conf status
listener_daemon                  RUNNING   pid 2164, uptime 0:02:22
sound_recorder     