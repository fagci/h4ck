#!/usr/bin/env python3

import logging
from fire import Fire

from lib.fuzz import Brute, Fuzz, ListFile
from lib.net import RTSPConnection, logger
from lib.scan import process_threaded


def process_host(interface, host):
    with RTSPConnection(host, 554, interface) as connection:
        for fuzz_result in Fuzz(connection):
            existing_path = fuzz_result.path

            if fuzz_result.ok:
                return connection.url(existing_path)

            if fuzz_result.auth_needed:
                for cred in Brute(connection, existing_path):
                    return connection.url(existing_path, cred)
                break


def brute(hosts_file: str, w: int = None, i: str = '', sp: bool = True, d: bool = False):
    from functools import partial

    if d:
        logger.setLevel(logging.DEBUG)
        h = logging.StreamHandler()
        logger.addHandler(h)

    hosts = ListFile(hosts_file)

    ph = partial(process_host, i)

    urls = process_threaded(ph, hosts, callback=lambda x: bool(x), workers=w)

    for url in urls:
        print(url)


if __name__ == "__main__":
    Fire(brute)
