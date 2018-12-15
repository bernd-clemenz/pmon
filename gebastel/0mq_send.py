#
# -*- coding: utf-8-*-
# Herumgebastel mit 0MQ
# This code will be reporting events to the response machine
#

import json
import socket
import time

import zmq


def make_send_str(msg):
    send = dict()
    send['created.ms'] = round(time.time() * 1000)
    send['msg'] = msg
    send['sender'] = socket.gethostname()
    return json.dumps(send)


context = zmq.Context(1)
try:
    sock = context.socket(zmq.REQ)
    try:
        # sock.connect('tcp://192.168.100.63:7777')
        sock.connect('tcp://127.0.0.1:7777')

        sock.send_string(make_send_str('hello'))
        response = sock.recv()

        print(response)

        sock.send_string(make_send_str('stop'))
        response = sock.recv()

        print(response)
    finally:
        sock.close()
finally:
    context.term()
