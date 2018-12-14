#
# -*- coding: utf-8-*-
# Herumgebastel mit 0MQ
# This code is the responder an an will implement the
# reactions to the requests, in case of pmon some error-handling
# strategies.
#

import json
import zmq


def read_message(msg):
    _msg = msg.decode('utf-8')
    return json.loads(_msg)


def handle_message(msg):
    if msg is None:
        return "none"
    return "ack"


# --------------------------------------------------------------------------------------------
context = zmq.Context(1)
try:
    sock = context.socket(zmq.REP)
    try:
        sock.bind('tcp://*:7777')

        go_on = True

        while go_on:
            message = read_message(sock.recv())
            print(message)
            response = handle_message(message)
            go_on = True if message['msg'] != 'stop' else False
            sock.send_string(response)
    finally:
        sock.close()
finally:
    context.term()
