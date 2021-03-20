#!/usr/bin/env python3
"""Find potentially vulnerable hosts on http 80 over all Internet"""

from fire import Fire

from lib.files import FUZZ_DIR
from lib.net import HTTPConnection
from lib.scan import generate_ips, process_each
from lib.utils import random_lowercase_alpha


FAKE_PATH = '/%s' % random_lowercase_alpha(3, 8)

VULNS_FILE = FUZZ_DIR / 'web_potential_vuln.txt'
VULNS = [ln.rstrip() for ln in VULNS_FILE.open()]


def check_ip(ip: str, pl, interface, verbose):
    with HTTPConnection(ip, 80, interface, 2, 5) as c:
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
            vulnerability = round(len(vulns) * 100 / len(VULNS), 1)
            if vulnerability > 75:
                return
            with pl:
                if verbose:
                    print('{:<15}'.format(ip), len(vulns), ', '.join(vulns))
                else:
                    print(ip)


def check_ips(c: int = 200000, w: int = 1024, i: str = '', v: bool = False):
    print('Tolal vulns:', len(VULNS))
    process_each(check_ip, generate_ips(c), w, i, v)


if __name__ == "__main__":
    try:
        Fire(check_ips)
    except KeyboardInterrupt:
        print('Interrupted by user')
