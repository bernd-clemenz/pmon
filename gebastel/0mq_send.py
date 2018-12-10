#
# -*- coding: utf-8-*-
# Herumgebastel mit 0MQ
#

import zmq

context = zmq.Context(1)
try:
    sock = context.socket(zmq.REQ)
    try:
        sock.bind('tcp://192.168.100.63:7777')

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
