#!/usr/bin/env python
from base64 import decodebytes
import os
import subprocess
import tempfile
from time import sleep

import requests

from lib.utils import sizeof_fmt

API_URL = 'https://www.vpngate.net/api/iphone/'
temp_file = os.path.join(tempfile.gettempdir(), 'vpn_servers.txt')


def main(country='', r=False):
    """Connect to VPN using openvpn

    :param str country: short country code
    :param bool r: refresh servers list"""

    if not r and os.path.exists(temp_file):
        with open(temp_file) as f:
            text = f.read()
    else:
        text = requests.get(API_URL).text
        with open(temp_file, 'w') as f:
            f.write(text)

    lines = text.splitlines()[1:]

    # HostName, IP, Score, Ping, Speed, CountryLong, CountryShort, NumVpnSessions, Uptime, TotalUsers, TotalTraffic, LogType, Operator, Message, OpenVPN_ConfigData_Base64]
    # labels = lines[0][1:].split(',')

    servers = [ln.split(',') for ln in lines[1:] if len(ln.split(',')) > 1]

    if country:
        servers = [s for s in servers if country.lower() == s[6].lower()]

    servers = sorted(servers, key=lambda s: s[4], reverse=True)[:20]

    for i, s in enumerate(servers):
        print(
            f'[{i}] Score: {s[2]}, ping: {s[3]}, speed {sizeof_fmt(int(s[4]),"B/s")}, country: {s[6]}')
    i = input(f'Choose server [0-{len(servers)-1}]: ')

    cfg = decodebytes(servers[0][-1].encode()).decode()

    _, fname = tempfile.mkstemp()

    with open(fname, 'w') as f:
        f.write(cfg)

    p = subprocess.Popen(['sudo', 'openvpn', '--config', fname])

    try:
        while True:
            sleep(60)
    except:
        p.kill()


if __name__ == "__main__":
    from fire import Fire
    Fire(main)
