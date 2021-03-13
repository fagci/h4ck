#!/usr/bin/env python3
"""Scan network (ex.: 192.168.0.1/24) for http(s) servers and get their titles."""

from ipaddress import ip_network

from bs4 import BeautifulSoup
from fire import Fire
from requests import get

from lib.scan import process_threaded


def test(host):
    # print(host)
    try:
        s = BeautifulSoup(get('http://%s' % host).text, 'lxml')
        title = s.title
        if title and not title.text:
            title = s.find('h1')
        if title:
            return '[+] %s:%d %s' % (host, 80, title.text)
    except:
        pass

    try:
        s = BeautifulSoup(get('https://%s' % host).text, 'lxml')
        title = s.title
        if title and not title.text:
            title = s.find('h1')
        if title:
            return '[+] %s:%d %s' % (host, 80, title.text)
    except:
        pass


def main(network: str, w: int = None):
    hosts = list(ip_network(network).hosts())
    results = process_threaded(test, hosts, workers=w)
    for result in results:
        if result:
            print(result)


if __name__ == "__main__":
    Fire(main)
