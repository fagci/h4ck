#!/usr/bin/env -S python -u
"""My fastest python native implementation of IP banners fortune"""
import re

from lib.scan import PORTS_WEB, check_port, generate_ports, get_banner, process, generate_ips

__author__ = 'Mikhail Yudin aka fagci'

title_re = re.compile(r'<title[^>]*?>([^<]+?)<', re.IGNORECASE)


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


BANNER_GETTERS = {
    80: get_meta,
    443: get_meta,
    21: get_banner,
    22: get_banner,
}


def get_banners(ip, ports):
    for port in ports:
        yield port, BANNER_GETTERS.get(port, get_banner)(ip, port)


def check_ip(ips, gen_lock, print_lock):
    while True:
        with gen_lock:
            try:
                ip = next(ips)
                ports = generate_ports(PORTS_WEB)
            except StopIteration:
                break
        ports = [port for port in ports if check_port(ip, port)]
        port_banners = list(get_banners(ip, ports))
        port_banners = list(filter(lambda b: b[1], port_banners))
        if port_banners:
            with print_lock:
                print(f'\n{ip}')
                print('  '+'\n  '.join(
                    f'{p:<4} {b}' for p, b in sorted(port_banners, key=lambda x: x[0])))


def check_ips(count: int, workers: int):
    ips = generate_ips(count)
    process(check_ip, ips, workers)


if __name__ == "__main__":
    check_ips(200000, 1024)
