#
# -*- coding: utf-8-*-
# Entry point of the simple process monitor.
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import argparse
import os
import sys

import cherrypy

import pmon
from pmon.srvr import PmonServer
from pmon.zmq_responder import ZmqResponder

if __name__ == '__main__':
    # Define arguments and read commandline
    parser = argparse.ArgumentParser(description="Simple process monitor.")
    parser.add_argument('--conf',
                        type=str,
                        default='pmon.ini',
                        help="the configuration file in INI-format")
    parser.add_argument('--server',
                        type=bool,
                        default=False,
                        help="Start the HTTP server. Exclusive parameter.")
    parser.add_argument('--nomail',
                        type=bool,
                        default=False,
                        help="Send no mail if set")
    parser.add_argument('--responder',
                        type=bool,
                        default=False,
                        help='Start the 0MQ based responder. Exclusive parameter.')
    args = parser.parse_args()

    pmon.init(args.conf)

    if args.server and args.responder:
        pmon.LOG.error("Whether server OR responder is allowed")
        sys.exit(1)
    
    if args.server:
        #
        # Launching the HTTP server
        #
        cherrypy.server.socket_host = pmon.CFG['pmon']['http.bind']
        cherrypy.server.socket_port = int(pmon.CFG['pmon']['http.port'])
        conf = {'/': {
                       'tools.sessions.on': False,
                       'tools.staticdir.root': os.path.abspath(os.getcwd())
                     },
                '/static': {
                             'tools.staticdir.on': True,
                             'tools.staticdir.dir': pmon.CFG['pmon']['http.static']
                           }
               }
        cherrypy.quickstart(PmonServer(pmon.LOG, pmon.CFG, args.nomail, pmon.execute_scan), '/', conf)
    elif args.responder:
        #
        # Launching the ZMQ responder
        #
        with ZmqResponder() as responder:
            responder.respond()
    else:
        # Process the checks
        pmon.execute_scan(args.nomail)
        pmon.LOG.info("done.")

    sys.exit(0)
