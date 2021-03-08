#!/usr/bin/env python3

from fire import Fire

from lib.fuzz import Brute, Fuzz
from lib.net import RTSPConnection


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
    with open(hosts_file) as hf:
        for ln in hf:
            result = process_host(ln.rstrip())
            if result:
                print(result)


if __name__ == "__main__":
    Fire(main)
