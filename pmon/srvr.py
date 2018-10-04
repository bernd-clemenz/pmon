#
# Embedded web-server, publishes latest results
# ans allows triggering a immediate rescan.
#
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import cherrypy
import json


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
    def scan(self):
        """
        Triggers rescan of process data.
        :return: same as index(self)
        """
        self.log.debug('Forced scan')
        if self.scan_callback is None:
            raise cherrypy.HTTPError(404)

        self.scan_callback(self.nomail_flag)
        return self.index()
