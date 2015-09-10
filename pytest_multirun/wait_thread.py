# -*- coding: utf-8 -*-
from threading import Thread
from multiprocessing.connection import Listener, Client


class WaitThread(Thread):
    def __init__(self, port_number, cb=None):
        Thread.__init__(self)
        self.port_number = port_number
        self.cb = cb

    def run(self):
        with Listener(('127.0.0.1', self.port_number)) as l:
            while True:
                with l.accept() as conn:
                    msg = conn.recv()
                    if msg == 'STOP':
                        break
                    else:
                        if self.cb:
                            self.cb(msg)
                        else:
                            print(msg)

    def stop(self):
        with Client(('127.0.0.1', self.port_number)) as conn:
            conn.send('STOP')
