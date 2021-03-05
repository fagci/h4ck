#!/usr/bin/env python3
from fire import Fire
from lib.net import RTSPConnection
from lib.fuzz import DictLoader, Fuzzer, Bruter


def brute(connection, path, C):
    with Bruter(connection, C, path) as bruter:
        for cred, ok in bruter:
            if ok:
                return cred


def fuzz(connection, P, C):
    with Fuzzer(connection, P) as fuzzer:
        print('[*] Fuzz')
        for path, auth in fuzzer:
            if auth:
                print('[*] Auth', path)
                cred = brute(connection, path, C)
                if cred:
                    yield connection.url(path, cred)
                else:
                    return
            else:
                yield connection.url(path)


def main(H, P, C):
    with DictLoader(H) as hosts:
        for host in hosts:
            print('Processing', host)
            with RTSPConnection(host, 554) as connection:
                for url in fuzz(connection, P, C):
                    print('[+]', url)


if __name__ == "__main__":
    Fire(main)
