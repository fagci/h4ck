#!/usr/bin/env python
"""Port scanner with multiple hosts and ports support"""
import ipaddress
import os
from random import shuffle

from fire import Fire

from lib.scan import check_port, process


def write_result(ip, port):
    while True:
        try:
            with open('local/netbat.txt', 'a') as f:
                f.write(f'{ip}:{port}\n')
            break
        except OSError as e:
            if e.errno == 24:
                from time import sleep
                sleep(0.15)
                continue
            print(e)


def get_ips(network, randomize=False):
    try:
        net = ipaddress.ip_network(network, strict=False)
        if randomize:
            hosts = list(net.hosts())
            shuffle(hosts)
            for host in hosts:
                yield str(host)
        else:
            for h in net.hosts():
                yield str(h)
    except ValueError as e:
        print(e)
        return


def ips_from_file(file, randomize=False):
    with open(file) as f:
        if randomize:
            f = list(f)
            shuffle(f)
        for ln in f:
            d = ln.rstrip()
            if '/' in d:
                for ip in get_ips(d, randomize):
                    yield ip
            else:
                yield d


def check_ip(ips, gl, pl, ports):
    while True:
        with gl:
            try:
                ip = next(ips)
            except StopIteration:
                break
        for port in ports:
            res = check_port(ip, int(port))
            if res:
                with pl:
                    print(f'{ip}:{port} ({int(res[1]*1000):>4} ms)')
                    write_result(ip, port)


def main(hosts, ports, workers=16, r=False):
    if isinstance(ports, int) or isinstance(ports, str):
        ports = str(ports)
        if '-' in ports:
            fp, tp = ports.split('-')
            ports = range(int(fp), int(tp))
        else:
            ports = ports.split(',')

    ips = []

    if os.path.exists(hosts):
        ips = ips_from_file(hosts, r)
    elif '/' in hosts:
        ips = get_ips(hosts, r)
    elif '-' in hosts:
        # fi, ti = hosts.split()
        print('Use /24 format please')
        exit()
    elif isinstance(hosts, str):
        ips = [hosts]
    else:
        ips = hosts

    process(check_ip, ips, workers, ports)


if __name__ == "__main__":
    Fire(main)
