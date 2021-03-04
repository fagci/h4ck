#!/usr/bin/env python3
from collections import defaultdict
from fire import Fire
from lib.scan import process, generate_ips, check_port, check_url

path_freqs = defaultdict(int)
file_name = 'path_freqs.txt'


def read_file():
    try:
        with open(file_name) as f:
            for ln in f:
                path, freq = ln.rstrip().split()
                path_freqs[path] = int(freq)
    except:
        pass


def write_file():
    with open(file_name, 'w') as f:
        for path, freq in path_freqs.items():
            f.write(f'{path} {freq}\n')


def inc(path):
    path_freqs[path] += 1


def check_ip(ips, gen_lock, print_lock):
    while True:
        with gen_lock:
            try:
                ip = next(ips)
            except StopIteration:
                break
        if check_port(ip, 80) and check_url(ip, 80, ''):
            with print_lock:
                print('[*]', ip)
            with open('data/web_fuzz.txt') as f:
                for ln in f:
                    path = ln.rstrip()
                    if check_url(ip, 80, path):
                        with print_lock:
                            print('[*]', ip, path)
                            inc(path)


def main(count=2000, workers=1024):
    read_file()
    process(check_ip, generate_ips(count), workers)
    write_file()


if __name__ == "__main__":
    Fire(main)
