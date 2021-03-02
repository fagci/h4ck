#!/usr/bin/env -S python -u
"""Find potentially vulnerable hosts on http 80 over all Internet"""
from random import randrange
from socket import socket
from typing import ContextManager, Optional
from fire import Fire
from lib.scan import generate_ips, process_each

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


class Connection(ContextManager):
    _c: Optional[socket] = None
    user_agent = 'Mozilla/5.0'

    def __init__(self, host, port, interface: str = ''):
        self.host = host
        self.port = port
        self.interface = interface

    def __enter__(self):
        from time import time, sleep
        from socket import create_connection, SOL_SOCKET, SO_BINDTODEVICE

        start = time()

        while time() - start < 3:
            try:
                self._c = create_connection((self.host, self.port), 1.5)
                if self.interface:
                    self._c.setsockopt(SOL_SOCKET, SO_BINDTODEVICE,
                                       self.interface.encode())
                break
            except KeyboardInterrupt:
                raise
            except OSError:
                sleep(1)

        return self

    def __exit__(self, exc_type, *_):
        if self._c:
            self._c.close()
        return exc_type is not KeyboardInterrupt

    def http_get(self, url, timeout=3):
        code = 999
        connection = self._c

        if connection:
            req = (
                'GET %s HTTP/1.1\r\n'
                'Host: %s\r\n'
                'User-Agent: %s\r\n'
                '\r\n\r\n'
            ) % (url, self.host, self.user_agent)

            try:
                connection.settimeout(timeout)
                connection.sendall(req.encode())

                res = connection.recv(128).decode()

                if res.startswith('HTTP/'):
                    code = int(res.split(None, 2)[1])
            except OSError:
                pass

        return code


def check_ip(ip, pl, interface):
    with Connection(ip, 80, interface) as c:
        # all queries handled by one script
        if c.http_get(FAKE_PATH) == 200:
            return

        vulns = []

        for url in VULNS:
            code = c.http_get(url)

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
