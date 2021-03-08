#!/usr/bin/env python3
"""Port scanner with multiple hosts and ports support"""
import ipaddress
import os
from random import shuffle

from fire import Fire

from lib.scan import check_port, process, process_each
from lib.utils import parse_range_list


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


def check_ip(ip, pl, ports, iface):
    for port in ports:
        res = check_port(ip, int(port), iface=iface)
        if res:
            with pl:
                print(f'{ip}:{port} ({int(res[1]*1000):>4} ms)')
                write_result(ip, port)


def main(hosts, ports, workers=16, r=False, i=None):
    """Scan ip, port range, ex.: ./netbat.py 192.168.0.1/24 8000-9000

    :param str hosts: CIDR or path to file w/hosts
    :param str ports: port, list or range ex.: 22-25, 80, 443, 8000-9000
    :param int workers: number of worker threads
    :param bool r: randomize ips
    :param str i: interface for scan"""
    if isinstance(ports, int) or isinstance(ports, str):
        ports = parse_range_list(str(ports))

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
        ips = iter([hosts])
    else:
        ips = iter(hosts)

    process_each(check_ip, ips, workers, ports, i)


if __name__ == "__main__":
    Fire(main)
