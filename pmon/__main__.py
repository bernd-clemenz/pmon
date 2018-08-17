#
# Entry point of the simple HTTP process monitor
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import argparse
import datetime
import logging
import logging.handlers
import json
import os
import requests
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


def init(config_name):
    global LOG, CFG, DATA

    # 1. Configuration
    if sys.version_info.major == 3:
        CFG = configparser.ConfigParser()
    elif sys.version_info.major == 2:
        CFG = ConfigParser.SafeConfigParser()
    else:
        raise Exception('Unsupported Python major version')

    CFG.read(config_name)

    # 2. Init logging
    LOG = logging.getLogger('pmon')
    LOG.setLevel(logging.DEBUG)
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


def datetime_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def check_url(cfg_name):
    global LOG, CFG, DATA
    url = CFG['urls'][cfg_name]
    LOG.info("Checking url: " + url)
    record = dict()
    try:
        record['time'] = datetime.datetime.now()
        rsp = requests.get(url, timeout=int(CFG['pmon']['timeout']))
        if rsp.status_code == requests.codes.ok:
            LOG.info("Check succeeded")
            record['result'] = 'SUCCESS'
            record['message'] = 'OK'
        else:
            LOG.warning("Check failed with status: " + str(rsp.status_code))
            record['result'] = 'APPLICATION_ERROR'
            record['message'] = rsp.status_code
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


def save_data():
    global LOG, CFG, DATA
    LOG.info('Writing result data')
    if len(DATA) > 0:
        with open(CFG['pmon']['data.file'], 'w') as f:
            f.write(json.dumps(DATA, indent=4, sort_keys=True, default=datetime_converter))


if __name__ == '__main__':
    # 1. Define arguments and read commandline
    parser = argparse.ArgumentParser(description="Simple process monitor")
    parser.add_argument('--conf', type=str, default='pmon.ini')
    args = parser.parse_args()

    init(args.conf)

    # 2. process the checks
    for n in CFG['urls'].keys():
        if n.startswith('url.'):
            check_url(n)

    # 3. post process results
    save_data()
