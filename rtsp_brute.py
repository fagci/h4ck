#!/usr/bin/env python3

import logging

from fire import Fire

from lib.fuzz import Brute, Fuzz, ListFile
from lib.net import RTSPConnection, logger
from lib.scan import threaded


def process_host(interface, host):
    try:
        with RTSPConnection(host, 554, interface) as connection:
            for fuzz_result in Fuzz(connection):
                existing_path = fuzz_result.path

                if fuzz_result.ok:
                    return connection.url(existing_path)

                if fuzz_result.auth_needed:
                    for cred in Brute(connection, existing_path):
                        return connection.url(existing_path, cred)
                    break
    except KeyboardInterrupt:
        print('ki')
        return False


def main(hosts_file: str, w: int = None, i: str = '', sp: bool = True, d: bool = False):
    from functools import partial

    if d:
        logger.setLevel(logging.DEBUG)
        h = logging.StreamHandler()
        logger.addHandler(h)

    hosts = ListFile(hosts_file)

    ph = partial(process_host, i)

    urls = threaded(ph, hosts, callback=bool, workers=w)

    print(*urls, sep='\n')


if __name__ == "__main__":
    Fire(main)
