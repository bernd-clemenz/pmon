#
# -*- coding: utf-8-*-
# Herumgebastel mit 0MQ
# This code will be reporting events to the resonse machine
#

import zmq

context = zmq.Context(1)
try:
    sock = context.socket(zmq.REQ)
    try:
        sock.connect('tcp://192.168.100.63:7777')

        sock.send_string('hello')
        response = sock.recv()

        print(response)

        sock.send_string('stop')
        response = sock.recv()

        print(response)
    finally:
        sock.close()
finally:
    context.term()
