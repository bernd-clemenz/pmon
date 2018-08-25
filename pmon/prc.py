#
# Methods to deal with a process list
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#
import urllib.parse
from paramiko import client


def ssh_command(log, clnt, command):
    """
    Execute a command on remote machine
    :param log: tje logger
    :param clnt: a valid ssh connection
    :param command: the command to issue
    :return: output of the command
    """
    if not clnt:
        log.error('Not connected')
        return None

    stdin, stdout, stderr = clnt.exec_command(command)
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            alldata = stdout.channel.recv(1024)
            prevdata = b"1"
            while prevdata:
                prevdata = stdout.channel.recv(1024)
                alldata += prevdata

            return str(alldata, 'utf-8')


def ssh_scan_process(cfg, log, url_key, data_store):
    """
    Read remote process list an scan for a given text snippet
    as indicator
    :param cfg: the configuration
    :param log: the logger
    :param url_key: config key to identify process
    :param data_store: store to put data in
    :return:
    """
    log.info("ssh connection and process scan: " + url_key)
    # Get process to scan for
    process = cfg['remote'][url_key + '.process']
    if process is None or process == '':
        log.warn('No process defined to scan for: ' + url_key)
        return
    # Fetch host from url
    url = cfg['urls'][url_key]
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc
    clnt = client.SSHClient()
    clnt.set_missing_host_key_policy(client.AutoAddPolicy())
    clnt.connect(host,
                 username=cfg['remote'][url_key + '.user'],
                 password=cfg['remote'][url_key + '.pwd'],
                 look_for_keys=False)
    try:
        result = ssh_command(log, clnt, cfg['remote'][url_key + '.scan_cmd'])
        if result is not None:
            lns = result.split('\n')
            fnd = list()
            for l in lns:
                if l.find(process, 0) >= 0:
                    fnd.append(l)
            data_store['ssh'] = fnd
            if len(fnd):
                log.info("found process entries for: " + url_key)
        else:
            log.error('No remote scan result')
            data_store['ssh'] = ['no ps result']
    finally:
        clnt.close()


def check_for_process(cfg, log, url_key, data_store):
    """
    Checking for processes, where configured.
    :param cfg: the configuration
    :param log: the logger
    :param url_key: key in config to identify process
    :param data_store: data container
    :return:
    """
    log.info("Checking for process " + url_key)

    # Connection type
    if (url_key + '.type') in cfg['remote']:
        con_type = cfg['remote'][url_key + '.type']
        if con_type == 'ssh':
            ssh_scan_process(cfg, log, url_key, data_store)
        else:
            log.info('Unsupported connection type: ' + con_type)
            return
    else:
        log.warning('No type entry')
