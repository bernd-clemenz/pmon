#
# -*- coding: utf-8-*-

import urllib

from paramiko import client


def _read_stream(stream):
    while not stream.channel.exit_status_ready():
        if stream.channel.recv_ready():
            all_data = stream.channel.recv(1024)
            prev_data = b"1"
            while prev_data:
                prev_data = stream.channel.recv(1024)
                all_data += prev_data

            return all_data


url = 'mysql://192.168.100.65'
parsed = urllib.parse.urlparse(url)
host = parsed.netloc
clnt = client.SSHClient()
clnt.load_system_host_keys()
clnt.set_missing_host_key_policy(client.AutoAddPolicy())
clnt.connect(host,
             username='pi',
             password='Max$Payn3',
             look_for_keys=False)
try:
    stdin, stdout, stderr = clnt.exec_command('sudo mysqladmin ping -u root -pisc123isc')
    s_out = _read_stream(stdout)
    s_out = s_out.decode('utf-8').strip() if s_out is not None else None
    s_err = _read_stream(stderr)
    s_err = s_err.decode('utf-8').strip() if s_err is not None else None
    print(s_out)
    print(s_err)
finally:
    clnt.close()
