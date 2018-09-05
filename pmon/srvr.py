#
# Methods to deal with a process list
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import cherrypy
import json
import os


class PmonServer(object):
    
    cfg = None
    log = None
    
    
    def __init__(self, log, cfg):
        self.cfg = cfg
        self.log = log
    
    @cherrypy.expose
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_out()
    def index(self):
        f_name = self.cfg['pmon']['latest.file']
        if f_name is None or f_name == '':
            raise cherrypy.HTTPError(500, 'Configuration error')
        try:    
            with open(f_name, 'r') as f:
                data = json.load(f)
            
            result = {'id': self.cfg['pmon']['id'], 'data': data }
            return result    
        except FileNotFoundError:
            raise cherrypy.HTTPError(404)