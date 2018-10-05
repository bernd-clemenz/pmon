#
# SSH based sensor on top of paramiko.
#
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#
import urllib.parse
from paramiko import client


class PmonSensor(object):

    @staticmethod
    def all_sensors(log, cfg, url_key, record):
        """
        Perform all scans at once
        :param log: the logger
        :param cfg:  current configuration
        :param url_key: config-key
        :param record: data container
        :return:
        """
        with PmonSensor(log, cfg, url_key, record) as sensor:
            sensor.scan_cmd()
            sensor.df()
            sensor.mem()

    """
    Reading some OS data via SSH from the target system.
    """
    log = None
    cfg = None
    url_key = None
    clnt = None
    record = None

    def __init__(self, log, cfg, url_key, record):
        """
        Constructor.
        :param log: the logger
        :param cfg: configuration data
        :param url_key: which url ti use from configuration
        :param record: data container
        """
        self.cfg = cfg
        self.log = log
        self.url_key = url_key
        self.record = record
        self.connect()

    def __enter__(self):
        """
        Allow use of 'with'
        :return: self
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Finalizer for with.
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.close()

    def connect(self):
        if not self.check():
            return
        url = self.cfg['urls'][self.url_key]
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc
        self.clnt = client.SSHClient()
        self.clnt.set_missing_host_key_policy(client.AutoAddPolicy())
        self.clnt.connect(host,
                          username=self.cfg['remote'][self.url_key + '.user'],
                          password=self.cfg['remote'][self.url_key + '.pwd'],
                          look_for_keys=False)
        self.log.debug("SSH sensor connected")

    def close(self):
        if self.clnt is not None:
            self.clnt.close()
            self.clnt = None
            self.log.debug("SSH sensor connection closed")

    def ssh_command(self, command):
        """
        Execute a command on remote machine.

        :param command: the command to issue
        :return: output of the command
        """
        if not self.clnt:
            self.log.error('Not connected')
            return None

        self.log.debug("Executing command: {0}".format(command))
        stdin, stdout, stderr = self.clnt.exec_command(command)
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                alldata = stdout.channel.recv(1024)
                prevdata = b"1"
                while prevdata:
                    prevdata = stdout.channel.recv(1024)
                    alldata += prevdata

                return str(alldata, 'utf-8')

    def check(self):
        """
        Check if a SSH connection is set
        :return: True if connection type is SSH, otherwise False
        """
        self.log.info("check before " + self.url_key)

        # Connection type
        if (self.url_key + '.type') in self.cfg['remote']:
            con_type = self.cfg['remote'][self.url_key + '.type']
            if con_type == 'ssh':
                return True
            else:
                self.log.info('Unsupported connection type: ' + con_type)
                return False
        else:
            self.log.warning('No type entry')
            return False

    def df(self):
        """
        A 'df' command. Add 'file.system' entry to record data
        :return:
        """

        df_data = self.ssh_command('df')
        self.record['file.system'] = df_data

    def mem(self):
        """
        A "egrep 'Mem|Cache|Swap' /proc/meminfo" command.
        Adds 'memory' entry to record data
        :return:
        """
        mem_data = self.ssh_command("egrep 'Mem|Cache|Swap' /proc/meminfo")
        self.record['memory'] = mem_data

    def scan_cmd(self):
        """
        Scan for the configured process marker with configured command
        :return:
        """
        process = self.cfg['remote'][self.url_key + '.process']
        if process is None or process == '':
            self.log.warn('No process defined to scan for: ' + self.url_key)
            self.record['ssh'] = ['no process marker configured']
            return
        result = self.ssh_command(self.cfg['remote'][self.url_key + '.scan_cmd'])
        if result is not None:
            # log.debug('Result: {0}'.format(result))
            lns = result.split('\n')
            fnd = list()
            for l in lns:
                if l.find(process, 0) >= 0:
                    fnd.append(l)
            self.record['ssh'] = fnd
            if len(fnd) > 0:
                self.log.info("found process entries for: " + self.url_key)
            else:
                self.log.debug('No matching process found')
                self.record['ssh'] = ['Process marker not found on remote machine']
        else:
            self.log.error('No remote scan result')
            self.record['ssh'] = ['no ps result at all']