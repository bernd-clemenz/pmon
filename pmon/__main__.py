#
# -*- coding: utf-8-*-
# Entry point of the simple HTTP process monitor.
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import argparse
import cherrypy
import os
import pmon
from pmon.srvr import PmonServer
import sys


if __name__ == '__main__':
    # 1. Define arguments and read commandline
    parser = argparse.ArgumentParser(description="Simple process monitor")
    parser.add_argument('--conf', type=str, default='pmon.ini')
    parser.add_argument('--server', type=bool, default=False)
    parser.add_argument('--nomail', type=bool, default=False)
    args = parser.parse_args()

    pmon.init(args.conf)
    
    if args.server:
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
    else:
        # 2. process the checks
        pmon.execute_scan(args.nomail)
        pmon.LOG.info("done.")

    sys.exit(0)
