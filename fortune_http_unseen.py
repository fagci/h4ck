#!/usr/bin/env python3
"""Grab sites which will not listed in search engines"""

import re

from fire import Fire

from lib.files import LOCAL_DIR
from lib.net import HTTPConnection
from lib.scan import generate_ips, process_each

LOG_FILE = LOCAL_DIR / 'http_unseen.txt'
DISALLOW_RE = re.compile(
    r'^User-agent:\s+\*$[\n\r]+^Disallow:\s+/$', re.IGNORECASE | re.MULTILINE)


def check_host(ip, lock):
    with HTTPConnection(ip, 80, timeout=1.5) as c:
        response = c.get('/robots.txt')
        if response.ok:
            if DISALLOW_RE.findall(response.body):
                with lock:
                    print(ip)
                    with LOG_FILE.open('a') as f:
                        f.write('%s\n' % ip)


def main(c=10_000_000, w=16):
    process_each(check_host, generate_ips(c), w)


if __name__ == "__main__":
    Fire(main)
