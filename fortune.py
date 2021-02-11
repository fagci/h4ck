#!/usr/bin/env -S python -u
"""My fastest python native implementation of IP http fortune"""
import socket as so
from threading import Lock, Thread
from random import randrange
from time import sleep
import re

__author__ = 'Mikhail Yudin aka fagci'

title_re = re.compile(r'<title[^>]*>([^<]+)', re.IGNORECASE)


gen_lock = Lock()
print_lock = Lock()


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


def get_meta(ip):
    from urllib.request import urlopen
    try:
        with urlopen(f'http://{ip}', timeout=1) as f:
            html = f.read(1024).decode()
            return title_re.findall(html)[0].strip().replace('\n', ' ').replace('\r', '')
    except:
        pass


def check_ip(ips):
    while True:
        with gen_lock:
            try:
                ip = next(ips)
            except StopIteration:
                break
        if check_port(ip, 80):
            title = get_meta(ip)
            if title:
                with print_lock:
                    print(ip, title)


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
