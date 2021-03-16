#!/usr/bin/env python3

from fire import Fire

from lib.files import FUZZ_DIR
from lib.net import HTTPConnection
from lib.scan import generate_ips, process_each


VULNS_FILE = FUZZ_DIR / 'http_cam.txt'
VULNS = [ln.rstrip() for ln in VULNS_FILE.open()]


def check_ip(ip: str, pl, interface):
    with HTTPConnection(ip, 80, interface, 2, 5) as c:
        for url in VULNS:
            response = c.get(url)
            if response.error:
                break
            if response.found and response.headers.get('content-type').startswith('image/'):
                with pl:
                    print('http://%s%s' % (ip, url))


def check_ips(c: int = 200000, w: int = 1024, i: str = ''):
    print('Tolal vulns:', len(VULNS))
    process_each(check_ip, generate_ips(c), w, i)


if __name__ == "__main__":
    try:
        Fire(check_ips)
    except KeyboardInterrupt:
        print('Interrupted by user')
