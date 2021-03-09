#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor, as_completed

from fire import Fire
from tqdm import tqdm

from lib.fuzz import Brute, Fuzz, ListFile
from lib.net import RTSPConnection
from lib.scan import process_threaded


def process_host(host):
    with RTSPConnection(host) as connection:
        for fuzz_result in Fuzz(connection):
            existing_path = fuzz_result.path

            if fuzz_result.ok:
                return connection.url(existing_path)
            elif fuzz_result.auth_needed:
                cred = Brute(connection, existing_path).run()
                if cred:
                    return connection.url(existing_path, cred)


def main(hosts_file):
    hosts = ListFile(hosts_file)

    urls = process_threaded(process_host, hosts)

    for url in urls:
        print(url)


if __name__ == "__main__":
    Fire(main)
