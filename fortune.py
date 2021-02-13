#!/usr/bin/env -S python -u
"""My fastest python native implementation of IP http fortune"""
import re
from urllib.request import urlopen

from lib.scan import check_port, generate_ips, process

__author__ = 'Mikhail Yudin aka fagci'

title_re = re.compile(r'<title[^>]*>([^<]+)', re.IGNORECASE)


def get_meta(ip):
    try:
        with urlopen(f'http://{ip}', timeout=1) as f:
            html = f.read(1024).decode().replace('\n', ' ').replace('\r', '')
            return title_re.findall(html)[0].strip()
    except:
        pass


def check_ip(ips, gen_lock, print_lock):
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
    ips = generate_ips(count)
    process(check_ip, ips, workers)


if __name__ == "__main__":
    check_ips(200000, 1024)
