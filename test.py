#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor, as_completed

from fire import Fire
from tqdm import tqdm

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
    urls = []
    with ThreadPoolExecutor(64) as ex:
        futures = []
        with open(hosts_file) as hf:
            for ln in hf:
                host = ln.rstrip()
                futures.append(ex.submit(process_host, host))

        with tqdm(total=len(futures)) as progress:
            for future in as_completed(futures):
                url = future.result()
                progress.update()
                if url:
                    urls.append(url)

    for url in urls:
        print(url)


if __name__ == "__main__":
    Fire(main)
