#!/usr/bin/env python3
from fire import Fire
from lib.net import RTSPConnection
from lib.fuzz import DictLoader, Fuzzer, Bruter
from concurrent.futures import ThreadPoolExecutor
from functools import partial


def brute(C, connection, path):
    with Bruter(connection, C, path) as bruter:
        for cred, ok in bruter:
            if ok:
                return cred


def fuzz(P, C, connection):
    with Fuzzer(connection, P) as fuzzer:
        print('[*] Fuzz')
        for path, auth in fuzzer:
            if auth:
                print('[*] Auth', path)
                cred = brute(C, connection, path)
                if cred:
                    yield connection.url(path, cred)
                else:
                    return
            else:
                yield connection.url(path)


def process_host(P, C, host):
    print('Processing', host)
    with RTSPConnection(host, 554) as connection:
        for url in fuzz(P, C, connection):
            print('[+]', url)


def main(H, P, C):
    with ThreadPoolExecutor(1024) as ex:
        with DictLoader(H) as hosts:
            ph = partial(process_host, P, C)
            for url in ex.map(ph, hosts):
                print(url)


if __name__ == "__main__":
    Fire(main)
