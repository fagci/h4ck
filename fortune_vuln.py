#!/usr/bin/env -S python -u
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

    def __exit__(self, *_):
        if self._c:
            return self._c.close()

    def http_get(self, url, timeout=3):
        code = 999

        if not self._c:
            return code

        req = (
            'GET %s HTTP/1.1\r\n'
            'Host: %s\r\n'
            'User-Agent: %s\r\n'
            '\r\n\r\n'
        ) % (url, self.host, self.user_agent)

        try:
            self._c.settimeout(timeout)
            self._c.sendall(req.encode())
            res = self._c.recv(1024).decode()
            if res.startswith('HTTP/'):
                _, code, _ = res.split(None, 2)
        except Exception:
            pass

        return int(code)


def check_ip(ip, pl, interface):
    for port in [80]:
        try:
            with Connection(ip, port, interface) as c:
                if c.http_get(FAKE_PATH) == 200:
                    return

                vulns = []

                for url in VULNS:
                    r = c.http_get(url)

                    if r == 999:
                        break

                    if r >= 500:
                        with pl:
                            print('!', ip, url)
                        break

                    if r == 200:
                        vulns.append(url)
                        with pl:
                            print('+', ip, url)

                if vulns:
                    with pl:
                        t = 'fake' if len(VULNS) == len(vulns) else 'real'
                        print('+', t, ip, vulns)
                    return

        except Exception as e:
            print(repr(e))
            pass


def check_ips(c: int = 200000, w: int = 1024, i: str = ''):
    process_each(check_ip, generate_ips(c), w, i)


if __name__ == "__main__":
    Fire(check_ips)
