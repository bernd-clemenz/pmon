#!/usr/bin/python3
# -*- coding: utf-8-*-
# Stop ZMQ responder.

import argparse
import socket
import time

import zmq

import pmon


def create_message(msg, msg_type):
    """
    General notification factory.
    :param msg: the text content of the message
    :param msg_type: the typeindicator
    :return: dictionary with message data
    """
    return {'created.ms': int(round(time.time() * 1000)),
            'msg.type': msg_type,
            'msg': msg,
            'from': socket.gethostname()}


if __name__ == '__main__':
    # Define arguments and read commandline
    parser = argparse.ArgumentParser(description="Simple process monitor.")
    parser.add_argument('--conf',
                        type=str,
                        default='pmon.ini',
                        help="the configuration file in INI-format")
    args = parser.parse_args()

    # init and establish connection, send the message
    pmon.init(args.conf)
    context = zmq.Context(1)
    try:
        sckt = context.socket(zmq.REQ)
        try:
            sckt.setsockopt(zmq.LINGER, 100)
            connection_str = "tcp://127.0.0.1:{0}".format(pmon.CFG['pmon']['zmq.port'])
            sckt.connect(connection_str)
            sckt.send_json(create_message('stop', 'INTERNAL'), zmq.DONTWAIT)
        finally:
            sckt.close()
    finally:
        context.term()
