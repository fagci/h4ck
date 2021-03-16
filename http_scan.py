#!/usr/bin/env python3
"""Scan network (ex.: 192.168.0.1/24) for http(s) servers and get their titles."""

from ipaddress import ip_network

from bs4 import BeautifulSoup
from fire import Fire
from requests import get

from lib.scan import threaded


def test(host, port=80):
    url = 'http%s://%s' % ('s' if port == 443 else '', host)

    try:
        s = BeautifulSoup(get(url).text, 'lxml')
        title = s.title

        if title and not title.text:
            title = s.find('h1')

        if title:
            return '[+] %s:%d %s' % (host, 80, title.text)

    except:
        pass


def main(network: str, w: int = None):
    ips = list(ip_network(network).hosts())
    print(*filter(bool, threaded(test, ips, workers=w)), sep='\n')


if __name__ == "__main__":
    Fire(main)
