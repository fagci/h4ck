#!/usr/bin/env -S python -u
"""My fastest python native implementation of IP http fortune"""
import socket as so
from threading import Lock, Thread
from random import randrange, shuffle
from time import sleep
import re

__author__ = 'Mikhail Yudin aka fagci'

title_re = re.compile(r'<title[^>]*>([^<]+)', re.IGNORECASE)


gen_lock = Lock()
print_lock = Lock()


def generate_ports():
    ports = [21, 22, 23, 25, 80, 139, 443, 445, 3306]
    shuffle(ports)
    return ports


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


def _get_title(html):
    return title_re.findall(html)[0].strip().replace('\n', ' ').replace('\r', '').replace('\t', ' ')


def get_meta(ip, port):
    from urllib.request import urlopen
    try:
        if port == 443:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            url = f'https://{ip}'
            with urlopen(url, timeout=0.3, context=ctx) as f:
                return _get_title(f.read(1024).decode())
        else:
            url = f'http://{ip}'
            with urlopen(url, timeout=0.3) as f:
                return _get_title(f.read(1024).decode())
    except Exception as e:
        # return e
        pass


def get_banner(ip, port):
    try:
        with so.socket() as s:
            if s.connect_ex((ip, port)) == 0:
                if port not in (21,):
                    s.send('Hello\r\n'.encode())
                banner = s.recv(1024).decode()
                for ln in banner.splitlines():
                    if any(x in ln.lower() for x in ('ssh', 'ftp', 'samba')) or (ln.strip()):
                        return ln.strip()
    except:
        pass


BANNER_GETTERS = {
    80: get_meta,
    443: get_meta,
    21: get_banner,
    22: get_banner,
}


def get_banners(ip, ports):
    for port in ports:
        yield port, BANNER_GETTERS.get(port, get_banner)(ip, port)


def check_ip(ips):
    while True:
        with gen_lock:
            try:
                ip = next(ips)
            except StopIteration:
                break
        ports = [port for port in generate_ports() if check_port(ip, port)]
        port_banners = list(get_banners(ip, ports))
        port_banners = list(filter(lambda b: b[1], port_banners))
        if port_banners:
            with print_lock:
                print(f'\n{ip}')
                print('  '+'\n  '.join(
                    f'{p:<4} {b}' for p, b in sorted(port_banners, key=lambda x: x[0])))


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
