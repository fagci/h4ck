#!/usr/bin/env python3

from functools import partial
import logging

from fire import Fire

from lib.fuzz import Brute, Fuzz, ListFile
from lib.net import RTSPConnection, logger
from lib.scan import threaded
from lib.models import add_result, add_path


def process_host(interface, brute, host):
    try:
        with RTSPConnection(host, 554, interface) as connection:
            for fuzz_result in Fuzz(connection):
                existing_path = fuzz_result.path

                if fuzz_result.ok:
                    add_path(host, 554, existing_path)
                    return connection.url(existing_path)

                if fuzz_result.auth_needed:
                    if brute:
                        for cred in Brute(connection, existing_path):
                            add_path(host, 554, existing_path, cred)
                            return connection.url(existing_path, cred)
                    else:
                        add_path(host, 554, existing_path, '?:')

                    break
    except KeyboardInterrupt:
        print('ki')
        return False


def main(hosts_file: str, brute: bool = False, w: int = None, i: str = '', sp: bool = True, d: bool = False):
    if d:
        logger.setLevel(logging.DEBUG)
        h = logging.StreamHandler()
        logger.addHandler(h)

    hosts = ListFile(hosts_file)

    ph = partial(process_host, i, brute)

    urls = threaded(ph, hosts, callback=bool, workers=w)

    print(*urls, sep='\n')


if __name__ == "__main__":
    Fire(main)
