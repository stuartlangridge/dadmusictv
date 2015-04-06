# https://gist.github.com/tito/7432757
from jnius import autoclass
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
UUID = autoclass('java.util.UUID')


import sys, socket, select, time
from Queue import Queue
import threading

class MPC_BTRFCOMM(object):

    def __init__(self, outq, host=None, port=None):
        self.host = host
        self.ready = False
        self.outq = outq
        self.sendq = []
        self.connect()

    def send(self, cmdidx, cmd):
        print "sending to socket %s %r" % (cmdidx, cmd)
        if not self.ready:
            print "Not sending; not ready yet"
            self.sendq.append((cmdidx, cmd))
            return
        self.cmd_current = cmdidx
        #self._sock.send(cmd)
        self.send_stream.write(cmd)
        self.send_stream.flush()

    def send_queued(self):
        while self.sendq:
            cmdidx, cmd = self.sendq.pop(0)
            print "sending queued command", cmdidx
            self.cmd_current = cmdidx
            self.send_stream.write(cmd)
            self.send_stream.flush()
            time.sleep(1)

    def socket_thread(self):
        self.cmd_current = 0
        #self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self._sock.connect((self.host, self.port))

        print "Looking to connect now"
        paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
        print "How many paired devices?", paired_devices
        self._sock = None
        for device in paired_devices:
            if device.getName() == self.host:
                self._sock = device.createRfcommSocketToServiceRecord(
                    UUID.fromString("62a52798-5d66-48c2-bd82-6e7c70078b70"))
        if not self._sock:
            print "Oh no couldn't get a socket!"
            sys.exit(1)
        print "got a socket; blocking until connect"
        try:
            self._sock.connect()
        except Exception, e:
            print "Couldn't connect to socket!", e
            sys.exit(2)
        print "connected to socket!"
        self.recv_stream = self._sock.getInputStream()
        self.send_stream = self._sock.getOutputStream()
        self.ready = True
        self.send_queued()

        resp = []
        while 1:
            c = self.recv_stream.available() 
            if c > 0:
                for i in range(c):
                    try:
                        resp.append(chr(self.recv_stream.read()))
                    except Exception, e:
                        print "There was an error reading from the read stream", e
                        break
                print "Got data from the stream: byte count", len(resp), "".join(resp)[:50], "..."
                self.outq.put((self.cmd_current, "".join(resp)))
                resp = []
            else:
                time.sleep(0.5)



    def connect(self):
        print "Connecting to host"
        socket_thr = threading.Thread(target=self.socket_thread)
        socket_thr.daemon = True
        socket_thr.start()

