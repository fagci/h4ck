#!/usr/bin/env -S python -u
from functools import partial
from lib.scan import check_port, check_url, process, generate_ips

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


def check_ip(ips, gen_lock, print_lock):
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
    ips = generate_ips(count)
    process(check_ip, ips, workers)


if __name__ == "__main__":
    check_ips(200000, 1024)
