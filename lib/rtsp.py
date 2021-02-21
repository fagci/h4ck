import re
import socket as so
from time import sleep
from urllib.parse import urlparse

status_re = re.compile(r'RTSP/\d\.\d (\d\d\d)')


def rtsp_req(url: str, timeout: float = 3, iface=None, retries=4):
    up = urlparse(url)
    req = (
        f'DESCRIBE {url} RTSP/1.0\r\n'
        'CSeq: 2\r\n'
        'Accept: application/sdp\r\n'
        '\r\n'
    )
    while True:
        try:
            with so.socket() as s:
                s.settimeout(timeout)
                if iface:
                    s.setsockopt(
                        so.SOL_SOCKET, so.SO_BINDTODEVICE, iface.encode())
                s.connect((up.hostname, up.port))
                s.sendall(req.encode())
                response = s.recv(1024).decode()
                return int(status_re.findall(response)[0])
        except so.timeout:
            return 503  # slowpoke, 3ff0ff
        except IOError as e:
            # 111 refused
            if e.errno == 111:
                return 500

            # 104 reset by peer
            if e.errno == 104:
                if retries <= 0:
                    return 500  # host f*ckup?
                sleep(2 / retries)
                retries -= 1
                continue

            # too many open files
            if e.errno == 24:
                sleep(0.15)
                continue

            # other errors
            return 500

        except KeyboardInterrupt:
            raise
        except IndexError:
            return 500  # not rtsp
        except Exception as e:
            # print('Unknown error:', e, 'please, contact with dev')
            return 500


def capture_image_cv2(stream_url, img_path):
    from cv2 import VideoCapture, imwrite
    vcap = VideoCapture(stream_url)
    if vcap.isOpened():
        ret, frame = vcap.read()
        vcap.release()
        if ret:
            imwrite(img_path, frame)
            return True
    return False


def capture_image_ffmpeg(stream_url, img_path):
    import ffmpeg

    stream = ffmpeg.input(stream_url, rtsp_transport='tcp')
    file = stream.output(img_path, vframes=1)

    try:
        file.run(capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error:
        return False
    else:
        return True


def capture_image(stream_url, img_path, prefer_ffmpeg=False):
    if prefer_ffmpeg:
        return capture_image_ffmpeg(stream_url, img_path)

    try:
        return capture_image_cv2(stream_url, img_path)
    except ImportError:
        return capture_image_ffmpeg(stream_url, img_path)
