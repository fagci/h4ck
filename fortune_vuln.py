#!/usr/bin/env -S python -u
"""Find potentially vulnerable hosts on http 80 over all Internet"""
from random import randrange
from fire import Fire
from lib.scan import generate_ips, process_each
from lib.net import HTTPConnection

__author__ = 'Mikhail Yudin aka fagci'

FAKE_PATH = '/%s' % ''.join(chr(randrange(ord('a'), ord('z')))
                            for _ in range(randrange(3, 16)))

print('Started with', FAKE_PATH, 'fake path')

VULNS = [
    '.env',
    '.htpasswd',
    '.htaccess',
    'composer.json',
    'README.md',
    'README.txt',
    'log.txt',
    'data.txt',
    'accounts.txt',
    'pass.txt',
    'passes.txt',
    'passwords.txt',
    'pazz.txt',
    'pazzezs.txt',
    'pw.txt',
    'technico.txt',
    'usernames.txt',
    'users.txt',
    '.gitignore',
]


def check_ip(ip, pl, interface):
    with HTTPConnection(ip, 80, interface, 1.5, 3) as c:
        # all queries handled by one script
        if c.get(FAKE_PATH) == 200:
            return

        vulns = []

        for url in VULNS:
            code = c.get(url)

            # internal error
            if code == 999:
                break

            # http server error
            if code >= 500:
                with pl:
                    print('E', ip, url)
                break

            if 200 <= code < 300:
                vulns.append(url)
                with pl:
                    print('+', ip, url)

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
