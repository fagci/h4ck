#!/usr/bin/env python3
"""My fastest python native implementation of IP http fortune"""
import re
from urllib.request import Request, urlopen

from lib.scan import check_port, generate_ips, process_each

__author__ = 'Mikhail Yudin aka fagci'

title_re = re.compile(r'<title[^>]*>([^<]+)', re.IGNORECASE)


def get_meta(ip):
    try:
        r: Request = Request('http://%s' % ip)
        r.add_header('User-Agent', 'Mozilla/5.0')
        with urlopen(r, timeout=1) as f:
            html = f.read(1024).decode()
            matches = title_re.findall(html)
            if matches:
                title = matches[0]
                title = title.replace('\n', ' ')
                title = title.replace('\r', '')
                return title.strip()
    except:
        pass


def check_ip(ip, print_lock):
    if check_port(ip, 80):
        title = get_meta(ip)
        if title:
            with print_lock:
                print(ip, title)


def check_ips(count: int, workers: int):
    process_each(check_ip, generate_ips(count), workers)


if __name__ == "__main__":
    try:
        check_ips(200000, 1024)
    except KeyboardInterrupt:
        print('Exit.')
