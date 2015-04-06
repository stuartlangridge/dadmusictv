#!/usr/bin/env python

import sys, socket, select, time
from Queue import Queue
import threading

class MPC_TCP(object):
    def __init__(self, outq, host, port):
        self.host = host
        self.port = int(port)
        self.outq = outq
        self.connect()

    def send(self, cmdidx, cmd):
        print "sending to socket %s %r" % (cmdidx, cmd)
        self.cmd_current = cmdidx
        self._sock.send(cmd)

    def socket_thread(self):
        self.cmd_current = 0
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self.host, self.port))
        self._sock.settimeout(1)
        resp = []
        while 1:
            try:
                data = self._sock.recv(4096)
            except socket.timeout, e:
                err = e.args[0]
                if err == "timed out":
                    if resp:
                        self.outq.put((self.cmd_current, "".join(resp)))
                        resp = []
                else:
                    print "There was some actual socket error", e
            except socket.error, e:
                print "There was a socket.error", e
            else:
                if len(data) == 0:
                    print "socket closed on server end"
                    break
                else:
                    resp.append(data)
        print "reconnecting"
        self.socket_thread()


    def connect(self):
        print "Connecting to", self.host, self.port
        socket_thr = threading.Thread(target=self.socket_thread)
        socket_thr.daemon = True
        socket_thr.start()

def monitor_outq(outq):
    while 1:
        cmdidx, response = outq.get(True)
        print "got outq entry, length is %s" % (len(response),)
        print "[%s] %s" % (cmdidx, response)

def shell(host, port):
    outq = Queue()
    mon_thr = threading.Thread(target=monitor_outq, args=(outq,))
    mon_thr.daemon = True
    mon_thr.start()

    c = MPC_TCP(host, port, outq)
    counter = 0
    while 1:
        counter += 1
        print ("[%s] Command please:" % counter),
        cmd = raw_input()
        if cmd == "quit": break
        c.send(counter, cmd + "\n")

if __name__ == "__main__":
    shell(*sys.argv[1:])