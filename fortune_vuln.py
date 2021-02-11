#!/usr/bin/env -S python -u
import warnings
import socket as so
from threading import Lock, Thread
from random import randrange
from time import sleep
from functools import partial

__author__ = 'Mikhail Yudin aka fagci'

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

gen_lock = Lock()
print_lock = Lock()


warnings.filterwarnings('ignore', message='Unverified HTTPS request')


def generate_ips(count: int):
    while count > 0:
        a = randrange(1, 256)
        b = randrange(0, 256)
        c = randrange(0, 256)
        d = randrange(1, 255)
        ip = f'{a}.{b}.{c}.{d}'
        if ip.startswith(('10.', '172.', '192.168.', '127.')):
            continue
        count -= 1
        yield ip


def check_port(ip, port):
    while True:
        try:
            with so.socket() as s:
                return s.connect_ex((ip, port)) == 0
        except so.error:
            continue


def check_url(ip, port, path):
    from requests import get
    s = 'https' if port == 443 else 'http'
    url = f'{s}://{ip}/{path}'
    try:
        r = get(url, allow_redirects=False, timeout=1, verify=False)
        return r.status_code == 200
    except:
        return False


def check_ip(ips):
    while True:
        with gen_lock:
            try:
                ip = next(ips)
            except StopIteration:
                break
        for port in [80]:
            if check_port(ip, port):
                cu = partial(check_url, ip, port)
                vulns_exists = map(cu, VULNS)
                if any(vulns_exists):
                    with print_lock:
                        print('[+]', ip, port)
                # else:
                #     with print_lock:
                #         print('[-]', ip, port)


def check_ips(count: int, workers: int):
    threads = []
    ips = generate_ips(count)

    for _ in range(workers):
        t = Thread(target=check_ip, daemon=True, args=(ips,))
        threads.append(t)

    for t in threads:
        t.start()

    while any(map(lambda t: t.is_alive(), threads)):
        sleep(0.25)


if __name__ == "__main__":
    so.setdefaulttimeout(0.18)
    check_ips(200000, 1024)
