#
# -*- coding: utf-8-*-
# receives messages via zmq and executes some simple
# operations.
#
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import json

import requests
import zmq

import pmon


class ZmqResponder(object):
    context = None
    socket = None

    def __init__(self):
        """
        Constructor.
        """
        self.cfg = pmon.CFG
        self.log = pmon.LOG

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.done()

    def bind(self):
        self.log.info("Binding ZMQ")
        port = self.cfg['pmon']['zmq.port']
        bind_str = "tcp://*:{0}".format(port)
        self.context = zmq.Context(1)
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(bind_str)

    def done(self):
        self.log.info("Disconnecting ZMQ")
        if self.socket is not None:
            self.socket.close()
        if self.context is not None:
            self.context.term()

    def _read_message(self):
        self.log.debug("Wait for incoming message")
        msg = self.socket.recv()
        _msg = msg.decode('utf-8')
        return json.loads(_msg)

    @staticmethod
    def _make_slack_payload(message):
        slack_payload = dict()
        slack_payload['text'] = message['msg']
        attachments = list()
        slack_payload['attachments'] = attachments

        attachment = dict()
        attachment["fallback"] = message['msg']
        attachment['text'] = message['msg']
        attachment['title'] = message['msg.type']
        attachment['author_name'] = message['from']

        attachments.append(attachment)
        return slack_payload

    def _report_message_to_slack(self, message):
        """
        Send a message to Slack Web-Hook.
        :param message: the message record to be send to slack
        :return:  None
        """
        self.log.debug("Forwarding message to slack")
        url = self.cfg['pmon']['slack.hook']
        payload = json.dumps(self._make_slack_payload(message))
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Content-Encoding': 'utf8',
                   'Content-Length': str(len(payload))}
        try:
            rsp = requests.post(url, data=payload, headers=headers)
            if rsp.status_code != requests.codes.ok:
                self.log.warn("problem sending to slack: {0}".format(rsp.status_code))
        except Exception as x:
            self.log.error(str(x))

    def respond(self):
        go_on = True
        while go_on:
            message = self._read_message()
            self.log.debug("Message: {0}, {1}".format(message['msg.type'],
                                                      message['msg']))
            self.socket.send_string('ACK')
            try:
                self._report_message_to_slack(message)
            except Exception as x:
                self.log.error(str(x))
            go_on = True if message['msg'] != 'stop' else False
