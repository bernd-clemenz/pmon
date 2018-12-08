#
# -*- coding: utf-8-*-
# Embedded web-server, publishes latest results
# and allows triggering a immediate rescan.
#
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import json

import cherrypy


class PmonServer(object):
    """
    Embedded server to display monitoring data.
    """
    cfg = None
    log = None
    nomail_flag = False
    scan_callback = None

    def __init__(self, log, cfg, nomail_flag, scan_callback):
        """
        Constructor.
        :param log: the logger
        :param cfg: the configuration
        :param nomail_flag: value of the nomail flag
        :param scan_callback: callback function for forced scan
        """
        self.cfg = cfg
        self.log = log
        self.nomail_flag = nomail_flag
        self.scan_callback = scan_callback

    @cherrypy.expose
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_out()
    def index(self):
        """
        Main data display content.
        :return: JSON data reed from latest result file
        """
        f_name = self.cfg['pmon']['latest.file']
        if f_name is None or f_name == '':
            raise cherrypy.HTTPError(500, 'Configuration error')
        try:    
            with open(f_name, 'r') as f:
                data = json.load(f)
            
            result = {'id': self.cfg['pmon']['id'], 'data': data}
            return result    
        except FileNotFoundError:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_out()
    def scan(self, notify=False):
        """
        Triggers rescan of process data.
        :param notify: value for the nomail flag given by web-user
        :return: same as index(self)
        """
        self.log.debug('Forced scan: {0}'.format(notify))
        if self.scan_callback is None:
            raise cherrypy.HTTPError(404)

        local_nomail_flag = self.nomail_flag
        if notify is not None:
            local_nomail_flag = not (notify == 'True')

        self.scan_callback(local_nomail_flag)
        return self.index()
