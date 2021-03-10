#!/usr/bin/env python3
import os

from fire import Fire

from lib.rtsp import capture_image
from lib.utils import geoip_str_online
from lib.utils import geoip_str_online, str_to_filename

DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIR = os.path.join(DIR, 'local')
DATA_DIR = os.path.join(DIR, 'data')
CAPTURES_DIR = os.path.join(LOCAL_DIR, 'rtsp_captures')


def capture(stream_url, prefer_ffmpeg=False, capture_callback=None):
    from urllib.parse import urlparse

    up = urlparse(stream_url)
    p = str_to_filename(f'{up.path}{up.params}')

    img_name = f'{up.hostname}_{up.port}_{up.username}_{up.password}_{p}'
    img_path = os.path.join(CAPTURES_DIR, f'{img_name}.jpg')

    captured = capture_image(stream_url, img_path, prefer_ffmpeg)

    print('[+]' if captured else '[-]', stream_url)

    if captured and capture_callback:
        import subprocess
        subprocess.Popen([capture_callback, stream_url,
                          img_path, geoip_str_online(up.hostname)]).communicate(timeout=25)


def main(urls_file, ff=False, cb=''):
    with open(urls_file) as f:
        for ln in f:
            url = ln.rstrip()
            capture(url, ff, cb)


if __name__ == "__main__":
    Fire(main)
