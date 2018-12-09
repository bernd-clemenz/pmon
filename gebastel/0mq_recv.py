#
# -*- coding: utf-8-*-
# Herumgebastel mit 0MQ
#

import zmq


def handle_message(msg):
    print(msg)
    return "done."


# --------------------------------------------------------------------------------------------
context = zmq.Context.instance()

sock = context.socket(zmq.REP)
sock.connect('tcp://127.0.0.1:7777')

go_on = True

while go_on:
    message = sock.recv()
    response = handle_message(message)
    go_on = True if message != b'stop' else False
    sock.send_string(response)
