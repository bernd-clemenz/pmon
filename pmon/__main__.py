#
# Entry point of the simple HTTP process monitor.
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import argparse
import cherrypy
import datetime
import json
import keyring
import logging
import logging.handlers
from email.mime.text import MIMEText
import os
import pmon.prc
from pmon.srvr import PmonServer
import requests
import smtplib
import sys
if sys.version_info.major == 3:
    import configparser
elif sys.version_info.major == 2:
    import ConfigParser
else:
    raise Exception('Unsupported Python major version')

LOG = None
CFG = None
DATA = None
THIS_RUN = None


def init(config_name):
    """
    Setup the application.
    :param config_name: name of the config file
    :return:
    """
    global LOG, CFG, DATA, THIS_RUN

    # 1. Configuration
    if sys.version_info.major == 3:
        CFG = configparser.ConfigParser()
    elif sys.version_info.major == 2:
        CFG = ConfigParser.SafeConfigParser()
    else:
        raise Exception('Unsupported Python major version')

    if not os.path.isfile(config_name):
        raise Exception('Config file not found: ' + config_name)
        
    CFG.read(config_name)

    # 2. Init logging
    LOG = logging.getLogger('pmon')
    lv_cfg = CFG['pmon']['log.level']
    lv_mp = {'INFO': logging.INFO,
             'WARN': logging.WARNING,
             'DEBUG': logging.DEBUG,
             'FATAL': logging.FATAL,
             'ERROR': logging.ERROR}
    if lv_cfg is not None and lv_cfg in lv_mp.keys():
        level = lv_mp[lv_cfg]
    else:
        level = logging.INFO
    LOG.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    rh = logging.handlers.RotatingFileHandler(CFG['pmon']['log.file'],
                                              maxBytes=1024 * 1024,
                                              backupCount=50)
    ch = logging.StreamHandler()
    rh.setFormatter(formatter)
    ch.setFormatter(formatter)
    LOG.addHandler(rh)
    LOG.addHandler(ch)
    LOG.info('PMON initialized(' + CFG['pmon']['id'] + ')')

    # 3. load data file
    if os.path.isfile(CFG['pmon']['data.file']) and os.path.getsize(CFG['pmon']['data.file']) > 0:
        with open(CFG['pmon']['data.file'], 'r') as f:
            DATA = json.load(f)
    else:
        DATA = dict()
        
    THIS_RUN = dict()    


def datetime_converter(o):
    """
    Converter for JSOn output
    :param o: value to convert to a string
    :return: string representation of the value
    """
    if isinstance(o, datetime.datetime):
        return o.__str__()


def check_url(cfg_name):
    """
    Do a GET query for url.
    :param cfg_name: name-part in config to read URL etc from
    :return:
    """
    global LOG, CFG, DATA, THIS_RUN
    url = CFG['urls'][cfg_name]
    LOG.info("Checking url: " + url)
    record = dict()
    try:
        record['time'] = datetime.datetime.now()
        rsp = requests.get(url, timeout=int(CFG['pmon']['timeout']))
        if rsp.status_code in [requests.codes.ok,
                               requests.codes.accepted,
                               requests.codes.created,
                               requests.codes.found,
                               requests.codes.unauthorized,
                               requests.codes.payment]:
            LOG.info("Check succeeded")
            record['result'] = 'SUCCESS'
            record['message'] = 'OK'
        else:
            LOG.warning("Check failed with status: " + str(rsp.status_code))
            record['result'] = 'APPLICATION_ERROR'
            record['message'] = rsp.status_code
            # perform additional operations
            pmon.prc.check_for_process(CFG, LOG, cfg_name, record)
    except Exception as x:
        LOG.error("Check failed due: " + str(x))
        record['result'] = 'EXCEPTION_ERROR'
        record['message'] = str(x)

    if url in DATA:
        DATA[url].append(record)
    else:
        url_lines = list()
        url_lines.append(record)
        DATA[url] = url_lines
        
    THIS_RUN[url] = record   


def save_data():
    """
    Write to result file
    :return:
    """
    global LOG, CFG, DATA, THIS_RUN
    LOG.info('Appending result data to collective file')
    if len(DATA) > 0:
        try:
            with open(CFG['pmon']['data.file'], 'w') as f:
                f.write(json.dumps(DATA, indent=2, sort_keys=True, default=datetime_converter))
        except Exception as x:
            LOG.error(str(x))
                
    LOG.info('Writing latest')        
    if len(THIS_RUN) > 0:
        try:
            with open(CFG['pmon']['latest.file'], 'w') as f:
                f.write(json.dumps(THIS_RUN, indent=2, sort_keys=True, default=datetime_converter))
        except Exception as x:
            LOG.error(str(x))
                
            
def notify():
    """
    Send email notifications to configured users.
    """
    global LOG, CFG, THIS_RUN
    LOG.info('Notifying user(s)')
    
    msg_text = json.dumps(THIS_RUN, indent=2, sort_keys=True, default=datetime_converter)
    msg = MIMEText(msg_text)
    msg['From'] = CFG.get('email', 'from')
    msg['To'] = CFG.get('email', 'to')
    msg['Subject'] = 'Monitored processes on {}'.format(CFG['pmon']['id'])
    s = smtplib.SMTP(CFG.get('email', 'server'), int(CFG.get('email', 'port')))
    LOG.debug("Mail server connected")
    try:
        #s.login(CFG.get('email', 'from'), keyring.get_password('pmon', 'email'))
        s.login(CFG.get('email', 'from'), CFG['email']['pwd'])
        s.sendmail(CFG.get('email', 'from'),
                   CFG.get('email', 'to').split(','),
                   msg.as_string())
        LOG.debug("mail send")
    except Exception as x:
        LOG.error(str(x))
    finally:
        s.quit()            


if __name__ == '__main__':
    # 1. Define arguments and read commandline
    parser = argparse.ArgumentParser(description="Simple process monitor")
    parser.add_argument('--conf', type=str, default='pmon.ini')
    parser.add_argument('--server', type=bool, default=False)
    parser.add_argument('--nomail', type=bool, default=False)
    args = parser.parse_args()

    init(args.conf)
    
    if args.server:
        cherrypy.server.socket_host = '0.0.0.0'
        cherrypy.config.update({'server.socket_port': int(CFG['pmon']['http.port'])})
        cherrypy.quickstart(PmonServer(LOG, CFG))
    else:
        # 2. process the checks
        for n in CFG['urls'].keys():
            if n.startswith('url.'):
                check_url(n)

        # 3. post process results
        save_data()
        if not args.nomail:
            notify()
        LOG.info("done.")
