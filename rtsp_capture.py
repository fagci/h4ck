#!/usr/bin/env python3
import os

from fire import Fire

from lib.rtsp import capture_image
from lib.utils import geoip_str_online
from lib.utils import geoip_str_online, str_to_filename
from lib.files import LOCAL_DIR

CAPTURES_DIR = LOCAL_DIR / 'rtsp_captures'


def capture(stream_url, prefer_ffmpeg=False, capture_callback=None):
    from urllib.parse import urlparse

    up = urlparse(stream_url)
    p = str_to_filename(f'{up.path}{up.params}')

    img_name = f'{up.hostname}_{up.port}_{up.username}_{up.password}_{p}'
    img_path = CAPTURES_DIR / ('%s.jpg' % img_name)

    captured = capture_image(stream_url, img_path, prefer_ffmpeg)

    print('[+]' if captured else '[-]', stream_url)

    if captured and capture_callback:
        import subprocess
        subprocess.Popen([capture_callback, stream_url,
                          str(img_path), geoip_str_online(up.hostname).encode().decode('ascii', errors='ignore')]).communicate(timeout=25)


def main(urls_file, ff=False, cb=''):
    if not CAPTURES_DIR.exists():
        CAPTURES_DIR.mkdir()

    with open(urls_file) as f:
        for ln in f:
            url = ln.rstrip()
            capture(url, ff, cb)


if __name__ == "__main__":
    Fire(main)
