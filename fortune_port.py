#!/usr/bin/env -S python -u
from time import sleep

from fire import Fire

from lib.scan import check_port, generate_ips, get_banner, process

__author__ = 'Mikhail Yudin aka fagci'


def check_ip(ips, gen_lock, print_lock, port, timeout, banner, file_path, double_check=False, interface=None):
    while True:
        with gen_lock:
            try:
                ip = next(ips)
            except StopIteration:
                break

        port_open_res = check_port(
            ip, port, timeout, double_check=double_check, iface=interface)
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
                        with open(file_path, 'a') as f:
                            f.write(f'{ip}\n')
                        break
                    except OSError:
                        sleep(0.25)
                        continue


def check_ips(port: int, count: int = 1_000_000, workers: int = 2048, timeout=1.5, banner=None, fresh=False, double_check=False, i=None):
    file_path = f'./local/hosts_{port}.txt'
    if fresh and input(f'Delete hosts_{port}.txt? y/n: ').lower() == 'y':
        import os
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except FileNotFoundError:
                print('No such file.')
            else:
                print('Removed.')
    ips = generate_ips(count)
    process(check_ip, ips, workers, port, timeout,
            banner, file_path, double_check, i)


if __name__ == "__main__":
    Fire(check_ips)
