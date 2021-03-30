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
TITLE_RE = re.compile(r'<title[^>]*>([^<]+)', re.IGNORECASE)
H1_RE = re.compile(r'<h1[^>]*>([^<]+)', re.IGNORECASE)


def check_host(ip, lock):
    with HTTPConnection(ip, 80, timeout=1.5) as c:
        response = c.get('/robots.txt')

        if not response.ok:
            return

        if not DISALLOW_RE.findall(response.body):
            return

    # coz connection closes often after 1st request
    with HTTPConnection(ip, 80) as c:
        page = c.get('/').body

        t_match = TITLE_RE.findall(page)
        h_match = H1_RE.findall(page)

        title = t_match[0] if t_match else h_match[0] if h_match else '-'
        title = title.strip().replace('\n', ' ').replace('\r', '')

        with lock:
            print(ip, title)
            with LOG_FILE.open('a') as f:
                f.write('%s %s\n' % (ip, title))


def main(c=10_000_000, w=16):
    process_each(check_host, generate_ips(c), w)


if __name__ == "__main__":
    Fire(main)
