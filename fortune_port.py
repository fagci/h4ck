#!/usr/bin/env -S python -u
from time import sleep

from fire import Fire

from lib.scan import check_port, generate_ips, get_banner, process

__author__ = 'Mikhail Yudin aka fagci'


def check_ip(ips, gen_lock, print_lock, port, timeout, banner):
    while True:
        with gen_lock:
            try:
                ip = next(ips)
            except StopIteration:
                break

        port_open_res = check_port(ip, port, timeout)
        if port_open_res:
            b = ''
            if banner:
                s = None
                if port == 554:
                    s = 'OPTIONS * RTSP/1.0\r\nCSeq: 1\r\n\r\n'
                b = get_banner(ip, port, send=s)
                if b and len(str(banner)) > 1 and str(banner) not in b:
                    continue
            with print_lock:
                print(f'{int(port_open_res[1]*1000):>4} ms', ip, b)
                while True:
                    try:
                        with open(f'./local/hosts_{port}.txt', 'a') as f:
                            f.write(f'{ip}\n')
                        break
                    except OSError:
                        sleep(0.25)
                        continue


def check_ips(port: int, count: int = 200000, workers: int = 2048, timeout=1, banner=None):
    ips = generate_ips(count)
    process(check_ip, ips, workers, port, timeout, banner)


if __name__ == "__main__":
    Fire(check_ips)
