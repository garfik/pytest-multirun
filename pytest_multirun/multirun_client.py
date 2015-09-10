# -*- coding: utf-8 -*-
from multiprocessing.connection import Listener, Client


class MultiRunClient(object):

    def __init__(self, port):
        self.port = int(port)

    def __send(self, msg):
        try:
            with Client(('127.0.0.1', self.port)) as conn:
                conn.send(msg)
        except ConnectionRefusedError:
            pass

    def add_to_report(self, nodeid, key, value=None):
        self.__send({
            'nodeid': nodeid,
            'type': 'extra',
            'key': key,
            'value': value
        })

    def send_report(self, rep):
        self.__send(rep)
