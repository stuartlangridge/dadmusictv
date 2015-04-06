= Dad Music TV =

Use a Raspberry Pi connected to a TV to play music, with that music stored on the SD card, the player controlled by Bluetooth from an Android phone, and no network at all required once it's running.

= Building for android =

We get buildozer as per http://kivy.org/docs/guide/packaging-android.html:

mkdir buildozer
cd buildozer
virtualenv ./venv # make a venv to install deps into
source ./venv/bin/activate
git clone https://github.com/kivy/buildozer.git
cd buildozer
python setup.py install

install cython, v0.21 because the latest 0.22 at time of writing has a bug (http://stackoverflow.com/questions/28674149/getting-error-mno-fused-madd-installing-kivy-in-virtualenv-over-fish-shell)

pip install cython=0.21

# change to the client folder for our app
cd ..../client
buildozer android debug deploy run # builds, deploys to plugged in android device, runs app

# the apk is in bin/ in the client folder
