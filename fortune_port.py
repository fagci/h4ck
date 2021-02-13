#!/usr/bin/env -S python -u
from fire import Fire
from lib.scan import check_port, generate_ips, get_banner, process

__author__ = 'Mikhail Yudin aka fagci'


def check_ip(ips, gen_lock, print_lock, port, banner):
    while True:
        with gen_lock:
            try:
                ip = next(ips)
            except StopIteration:
                break

        if check_port(ip, port):
            b = ''
            if banner:
                s = None
                if port == 554:
                    s = 'OPTIONS * RTSP/1.0\r\nCSeq: 1\r\n\r\n'
                b = get_banner(ip, port, send=s)
                if b and len(str(banner)) > 1 and str(banner) not in b:
                    continue
            with print_lock:
                print(ip, b)
                with open(f'./local/hosts_{port}.txt', 'a') as f:
                    f.write(f'{ip}\n')


def check_ips(port: int, count: int = 200000, workers: int = 1024, banner=None):
    ips = generate_ips(count)
    process(check_ip, ips, workers, port, banner)


if __name__ == "__main__":
    Fire(check_ips)
