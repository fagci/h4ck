#!/usr/bin/env python3

from fire import Fire

from lib.scan import get_domains_from_cert
from lib.utils import geoip_str_online, reverse_dns


def main(host):
    print('Location:', geoip_str_online(host))
    print('rDNS:', reverse_dns(host))
    print('Domains by cert:', ', '.join(get_domains_from_cert(host)))


if __name__ == '__main__':
    Fire(main)
