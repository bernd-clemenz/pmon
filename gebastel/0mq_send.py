#
# -*- coding: utf-8-*-
# Herumgebastel mit 0MQ
#

import zmq

context = zmq.Context.instance()

sock = context.socket(zmq.REQ)
sock.bind('tcp://*:7777')

sock.send_string('hello')
response = sock.recv()

print(response)

sock.send_string('stop')
response = sock.recv()

print(response)
