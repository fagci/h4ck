#!/usr/bin/env python3
from fire import Fire
from lib.net import RTSPConnection
from lib.fuzz import DictLoader, Fuzzer, Bruter


def main(H, P, C):
    with DictLoader(H) as hosts:
        for host in hosts:
            print('Processing', host)
            with RTSPConnection(host, 554) as connection:
                with Fuzzer(connection, P) as fuzzer:
                    print('Fuzz')
                    for path, auth in fuzzer:
                        if auth:
                            print('Auth needed')
                            with Bruter(connection, C, path) as bruter:
                                for cred, ok in bruter:
                                    if ok:
                                        print('  [+]', cred)
                                        break
                                    else:
                                        print('  [-]', cred)
                        else:
                            print('[+]', path)


if __name__ == "__main__":
    Fire(main)
