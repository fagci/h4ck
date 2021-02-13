#!/usr/bin/env -S python -u
from fire import Fire
from lib.scan import check_port, generate_ips, process

__author__ = 'Mikhail Yudin aka fagci'


def check_ip(ips, gen_lock, print_lock, port):
    while True:
        with gen_lock:
            try:
                ip = next(ips)
            except StopIteration:
                break
        if check_port(ip, port):
            with print_lock:
                with open(f'./local/hosts_{port}.txt', 'a') as f:
                    f.write(f'{ip}\n')

                print(ip)


def check_ips(port: int, count: int = 200000, workers: int = 1024):
    ips = generate_ips(count)
    process(check_ip, ips, workers, port)


if __name__ == "__main__":
    Fire(check_ips)
