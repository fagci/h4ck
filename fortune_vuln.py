#!/usr/bin/env -S python -u
"""Find potentially vulnerable hosts on http 80 over all Internet"""
from lib.utils import random_lowercase_alpha
import logging
from fire import Fire
import os
from lib.scan import generate_ips, process_each
from lib.net import HTTPConnection, logger

__author__ = 'Mikhail Yudin aka fagci'

logger.setLevel(logging.DEBUG)

FAKE_PATH = '/%s' % random_lowercase_alpha(3, 16)

print('Started with', FAKE_PATH, 'fake path')

DIR = os.path.dirname(os.path.abspath(__file__))
VULNS_FILE = os.path.join(DIR, 'data', 'web_potential_vuln.txt')
VULNS = [ln.rstrip() for ln in open(VULNS_FILE)]


def check_ip(ip, pl, interface):
    with HTTPConnection(ip, 80, interface, 1.5, 3) as c:
        # all queries handled by one script
        if c.get(FAKE_PATH).ok:
            return

        vulns = []

        for url in VULNS:
            response = c.get(url)

            if response.error:
                break

            if response.found:
                vulns.append(url)

        if vulns:
            t = 'fake' if len(VULNS) == len(vulns) else 'real'
            with pl:
                print('+', t, ip, vulns)
            return


def check_ips(c: int = 200000, w: int = 1024, i: str = ''):
    process_each(check_ip, generate_ips(c), w, i)


if __name__ == "__main__":
    try:
        Fire(check_ips)
    except KeyboardInterrupt:
        print('Interrupted by user')
