#
# SSH based sensor on top of paramiko.
#
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#
import urllib.parse
from paramiko import client


class PmonSensor(object):
    """
    Reading some OS data via SSH from the target system.
    """
    log = None
    cfg = None
    url_key = None
    clnt = None

    def __init__(self, log, cfg, url_key):
        """
        Constructor.
        :param log: the loggeer
        :param cfg: configuration data
        :param url_key: which url ti use from configuration
        """
        self.cfg = cfg
        self.log = log
        self.url_key = url_key
        self.connect()

    def connect(self):
        url = self.cfg['urls'][self.url_key]
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc
        self.clnt = client.SSHClient()
        self.clnt.set_missing_host_key_policy(client.AutoAddPolicy())
        self.clnt.connect(host,
                          username=self.cfg['remote'][self.url_key + '.user'],
                          password=self.cfg['remote'][self.url_key + '.pwd'],
                          look_for_keys=False)

    def df(self):
        pass
