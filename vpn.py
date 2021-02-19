#!/usr/bin/env python
import os
import requests
import tempfile

API_URL = 'https://www.vpngate.net/api/iphone/'
temp_file = os.path.join(tempfile.gettempdir(), 'vpn_servers.txt')


def main(country=''):

    if os.path.exists(temp_file):
        with open(temp_file) as f:
            text = f.read()
    else:
        text = requests.get(API_URL).text
        with open(temp_file, 'w') as f:
            f.write(text)

    lines = text.splitlines()[1:]

    labels = lines[0][1:].split(',')

    servers = [ln.split(',') for ln in lines[1:] if ln]
    print(servers[0])
    # HostName, IP, Score, Ping, Speed, CountryLong, CountryShort, NumVpnSessions, Uptime, TotalUsers, TotalTraffic, LogType, Operator, Message, OpenVPN_ConfigData_Base64]

    if country:
        servers = [s for s in servers if country.lower() == s[6].lower()]

    servers = sorted(servers, key=lambda s: s[2], reverse=True)[:10]

    print(servers)


if __name__ == "__main__":
    from fire import Fire
    Fire(main)
