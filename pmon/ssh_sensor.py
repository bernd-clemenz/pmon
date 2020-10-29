#
# -*- coding: utf-8-*-
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
        :return: None
        """
        try:
            with PmonSensor(log, cfg, url_key, record) as sensor:
                sensor.scan_cmd()
                sensor.df_size()
                sensor.mem()
                sensor.scan_logs()
        except Exception as x:
            log.error("All ssh-sensors: " + str(x))

    """
    Reading some OS data via SSH from the target system.
    Cleanup requires call to 'close()'
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
        :param url_key: which url to use from configuration
        :param record: data container
        """
        self.cfg = cfg
        self.log = log
        self.url_key = url_key
        self.record = record

    def __enter__(self):
        """
        Allow use of 'with', connects with remote system
        :return: self
        """
        if self.__connect():
            return self
        raise Exception("Failed to connect")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Finalizer for with.
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.close()

    def __add_to_ssh_message(self, msg):
        """
        Adding a text to the 'ssh'-key values in the
        'record' data container.
        :param msg: the message to add
        :return:
        """
        if msg is None or msg == '':
            return

        if 'ssh' in self.record:
            messages = self.record['ssh']
        else:
            messages = list()
            self.record['ssh'] = messages

        messages.append(msg)

    def __connect(self):
        """
        Create a ssh client and store it in member variable.
        :return: True if connected, otherwise False
        """
        if not self.__check() or self.clnt is not None:
            return False

        url = self.cfg['urls'][self.url_key]
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc
        self.clnt = client.SSHClient()
        self.clnt.load_system_host_keys()
        self.clnt.set_missing_host_key_policy(client.AutoAddPolicy())
        self.clnt.connect(host,
                          username=self.cfg['remote'][self.url_key + '.user'],
                          password=self.cfg['remote'][self.url_key + '.pwd'],
                          look_for_keys=False)
        self.log.debug("SSH sensor connected: {0}".format(host))
        return True

    def close(self):
        if self.clnt is not None:
            try:
                self.clnt.close()
            finally:
                self.clnt = None
                self.log.debug("SSH sensor connection closed")

    def __ssh_command(self, command):
        """
        Execute a command on remote machine.

        :param command: the command to issue
        :return: output of the command
        """

        def __read_stream(stream):
            while not stream.channel.exit_status_ready():
                if stream.channel.recv_ready():
                    all_data = stream.channel.recv(1024)
                    prev_data = b"1"
                    while prev_data:
                        prev_data = stream.channel.recv(1024)
                        all_data += prev_data

                    if all_data is not None:
                        all_data = all_data.decode('utf-8').strip()

                    return all_data

        if not self.clnt:
            self.log.error('Not connected')
            self.__add_to_ssh_message('Not connected')
            return None

        self.log.debug("Executing command: {0}".format(command))
        try:
            stdin, stdout, stderr = self.clnt.exec_command(command)
            all_data = __read_stream(stdout)

            self.log.debug(all_data)
            return all_data
        except Exception as x:
            self.log.error(str(x))
            self.__add_to_ssh_message(str(x))

    def __check(self):
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
            self.log.warning('No type entry: ' + self.url_key)
            return False

    def df_size(self):
        """
        A 'df' command. Add 'file.system' entry to record data
        :return:
        """
        df_data = self.__ssh_command('df')
        self.record['file.system'] = df_data

    def mem(self):
        """
        A "egrep 'Mem|Cache|Swap' /proc/meminfo" command.
        Adds 'memory' entry to record data
        :return:
        """
        mem_data = self.__ssh_command("egrep 'Mem|Cache|Swap' /proc/meminfo")
        self.record['memory'] = mem_data

    def scan_cmd(self):
        """
        Scan for the configured process marker with configured command
        :return:
        """
        process = self.cfg['remote'][self.url_key + '.process']
        if process is None or process == '':
            self.log.warn('No process defined to scan for: ' + self.url_key)
            self.__add_to_ssh_message('no process marker configured')
            return
        result = self.__ssh_command(self.cfg['remote'][self.url_key + '.scan_cmd'])
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
                self.__add_to_ssh_message('Process marker not found on remote machine')
        else:
            self.log.error('No remote scan result')
            self.__add_to_ssh_message('no ps result at all')

    def scan_mysql(self):
        command = self.cfg['remote'][self.url_key + '.scan_cmd']
        if command is None or command == '':
            self.log.warn('No scan_cmd defined to scan for: ' + self.url_key)
            self.__add_to_ssh_message('no scan_cmd configured')
            return
        self.log.info("Executing configured command")
        result = self.__ssh_command(self.cfg['remote'][self.url_key + '.scan_cmd'])
        if 'mysqld is alive' in result:
            self.log.info("Check succeeded")
            self.record['result'] = 'SUCCESS'
            self.record['message'] = 'OK'
        else:
            self.log.warning("Check failed with status: " + result)
            self.record['result'] = 'APPLICATION_ERROR'
            self.record['message'] = result

    def scan_logs(self):
        """
        Scan log files using grep on remote machine
        :return:
        """
        self.log.debug('Scan log files')
        pattern = self.cfg['remote'][self.url_key + '.log.pattern']
        log_dir = self.cfg['remote'][self.url_key + '.log.dir']
        log_files = self.cfg['remote'][self.url_key + '.log.files']
        if pattern is None or log_dir is None or log_files is None:
            self.log.info('No log file scan configured or incomplete')
            self.__add_to_ssh_message('No log file scan configured or incomplete')
            return
        cmd = 'grep -i "{0}" {1}/{2}'.format(pattern, log_dir, log_files)
        grep = self.__ssh_command(cmd)
        self.record['logs'] = grep
