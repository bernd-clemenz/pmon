#
# -*- coding: utf-8-*-
# Simple process monitor core functions.
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import configparser
import datetime
import json
import logging
import logging.handlers
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

import requests

from pmon.srvr import PmonServer
from pmon.ssh_sensor import PmonSensor

name = 'pmon'

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
    CFG = configparser.ConfigParser()

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


def __datetime_converter(o):
    """
    Converter for JSON output
    :param o: value to convert to a string
    :return: string representation of the value
    """
    if isinstance(o, datetime.datetime):
        return o.__str__()


def __http_scan(cfg_name):
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
            PmonSensor.all_sensors(LOG, CFG, cfg_name, record)
    except Exception as x:
        LOG.error("Check failed due: " + str(x))
        record['result'] = 'EXCEPTION_ERROR'
        record['message'] = str(x)
        PmonSensor.all_sensors(LOG, CFG, cfg_name, record)
    if url in DATA:
        DATA[url].append(record)
    else:
        url_lines = list()
        url_lines.append(record)
        DATA[url] = url_lines

    THIS_RUN[url] = record


def __check_ssh(cfg_name):
    global LOG, CFG, DATA, THIS_RUN
    url = CFG['urls'][cfg_name]
    LOG.info("Checking url: " + url)
    record = dict()
    record['time'] = datetime.datetime.now()
    try:
        with PmonSensor(LOG, CFG, cfg_name, record) as s:
            s.scan_mysql()
    except Exception as x:
        record['result'] = 'EXCEPTION_ERROR'
        record['message'] = str(x)
    THIS_RUN[url] = record


def check_url(cfg_name):
    """
    Do a GET query for url. part of the core of the application.
    :param cfg_name: name-part in config to read URL etc from
    :return:
    """
    global LOG, CFG, DATA, THIS_RUN
    url = CFG['urls'][cfg_name]
    if url.startswith('http'):
        __http_scan(cfg_name)
    elif url.startswith('mysql'):
        __check_ssh(cfg_name)


def __save_data():
    """
    Write to result file
    :return:
    """
    global LOG, CFG, DATA, THIS_RUN
    LOG.info('Appending result data to collective file')
    if len(DATA) > 0:
        try:
            with open(CFG['pmon']['data.file'], 'w') as f:
                f.write(json.dumps(DATA, indent=2, sort_keys=True, default=__datetime_converter))
        except Exception as x:
            LOG.error(str(x))

    LOG.info('Writing latest')
    if len(THIS_RUN) > 0:
        try:
            with open(CFG['pmon']['latest.file'], 'w') as f:
                f.write(json.dumps(THIS_RUN, indent=2, sort_keys=True, default=__datetime_converter))
        except Exception as x:
            LOG.error(str(x))


def __prepare_text_mail():
    """
    :return: a MimeText with the data als plain text
    """
    global LOG, CFG, THIS_RUN
    LOG.debug("prepare text message")
    text_msg = list()
    text_data_template = Template("$result, $time, $message")
    for url, details in THIS_RUN.items():
        line = url + " | " + text_data_template.substitute(details)
        text_msg.append(line)

    text_out_msg = "ISC PMON process monitoring.\n" + "\n".join(text_msg)
    return MIMEText(text_out_msg, 'plain')


def __prepare_html_mail():
    """
    :return: the status as HTML message
    """
    global LOG, CFG, THIS_RUN
    LOG.debug("prepare html message")
    html_data_line = Template('<tr><td><a href="$url" target="_blank">$url</a></td>$details</tr>')
    html_data_template_ok = Template(
        '<td style="text-align: center; color: #4CAF50; font-weight: bold;">$result</td><td>$time</td><td>$message</td>')
    html_data_template_fail = Template(
        '<td style="text-align: center; color: #FF0000; font-weight: bold;">$result</td><td>$time</td><td>$message</td>')

    html_lines = list()
    for url, details in THIS_RUN.items():
        if details['result'] == 'SUCCESS':
            html_details = html_data_template_ok.substitute(details)
        else:
            html_details = html_data_template_fail.substitute(details)
        line_data = {'url': url, 'details': html_details}
        html_lines.append(html_data_line.substitute(line_data))

    html_inner = '\n'.join(html_lines)
    html_outer = '''
    <!DOCTYPE html>
    <html>
    <head>
      <title>process status</title>
      <style>
        body {{
        font-family: Verdana, Sans-Serif;
        font-size: small;
      }}
        table {{
          border-collapse: collapse;
       }}
        table, th, td {{
          border: 1px solid black;
          margin: 5px;
          padding-left: 5px;
          padding-right: 5px;
        }}
        tr:nth-child(even) {{background-color: #f2f2f2;}}
        tr:hover {{background-color: #e1e1e1;}}
        th {{
          background-color: #4CAF50;
          color: white;
      }}
      </style>
    </head>
    <body>
      <h3>ISC PMON process monitoring</h3>
      <table>
        <thead>
          <tr>
            <th>URL</th><th>Status</th><th>Time</th><th>Message</th>
          </tr>
          {0}
        </thead>
      </table>
      <p style="text-align: center; font-size: xx-small;">
        &copy; 2018 ISC Clemenz &amp; Weinbrecht GmbH
      </p>
    </body>
    </html>
    '''.strip().format(html_inner)
    return MIMEText(html_outer, 'html')


def __prepare_message_parts():
    """
    :return: a combined MIME multipart message
    """
    global LOG, CFG, THIS_RUN
    LOG.debug("prepare multipart mail message")
    mail_msg = MIMEMultipart('alternative')
    mail_msg['Subject'] = 'Monitored processes on {}'.format(CFG['pmon']['id'])
    mail_msg['From'] = CFG.get('email', 'from')
    mail_msg['To'] = CFG.get('email', 'to')
    # Last entry ist the preferred one to display
    mail_msg.attach(__prepare_text_mail())
    mail_msg.attach(__prepare_html_mail())
    return mail_msg


def notify():
    """
    Send email notifications to configured users.
    """
    global LOG, CFG, THIS_RUN
    LOG.info('Notifying user(s)')

    # msg_text = json.dumps(THIS_RUN, indent=2, sort_keys=True, default=__datetime_converter)
    msg = __prepare_message_parts()  # MIMEText(msg_text)

    s = smtplib.SMTP(CFG.get('email', 'server'), int(CFG.get('email', 'port')))
    LOG.debug("Mail server connected")
    try:
        # s.login(CFG.get('email', 'from'), keyring.get_password('pmon', 'email'))
        s.login(CFG.get('email', 'from'), CFG['email']['pwd'])
        s.sendmail(CFG.get('email', 'from'),
                   CFG.get('email', 'to').split(','),
                   msg.as_string())
        LOG.debug("mail send")
    except Exception as x:
        LOG.error(str(x))
    finally:
        s.quit()


def execute_scan(nomail_flag):
    """
    Does the main work of working through the URL-list.
    :param nomail_flag: value of the flag
    :return: None
    """
    global LOG, CFG, THIS_RUN
    LOG.debug('scan ... ')

    for n in CFG['urls'].keys():
        if n.startswith('url.'):
            check_url(n)

    # 3. post process results
    __save_data()
    if not nomail_flag:
        notify()
