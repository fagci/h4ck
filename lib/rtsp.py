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
                response = s.recv(256).decode()
                return int(status_re.findall(response)[0])
        except so.timeout:
            return 408  # slowpoke, 3ff0ff
        except IOError as e:
            # 111 refused
            if e.errno == 111:
                return 444

            # 104 reset by peer
            if e.errno == 104:
                if retries <= 0:
                    return 503  # host f*ckup?
                sleep(2 / retries)
                retries -= 1
                continue

            # too many open files
            if e.errno == 24:
                sleep(0.15)
                continue

            # other errors
            print(f'IO err {e} for {url}')
            return 500

        except KeyboardInterrupt:
            raise
        except IndexError:
            # print(f'Bad response: {response}')
            return 500  # not rtsp or not by RFC
        except Exception as e:
            print('Unknown error:', e,
                  f'Url: {url}. Please, contact with dev')
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


def capture_image_av(stream_url, img_path):
    import av
    options = {
        'rtsp_transport': 'tcp',
        'rtsp_flags': 'prefer_tcp',
        'stimeout': '60000000',
    }
    try:
        with av.open(stream_url, options=options, timeout=20) as c:
            vs = c.streams.video[0]
            if vs.profile is not None and vs.codec_context.format and vs.start_time is not None:
                vs.thread_type = "AUTO"
                for frame in c.decode(video=0):
                    frame.to_image().save(img_path)
                    return True

    except Exception as e:
        # print('[E]', stream_url, repr(e))
        pass

    return False


def capture_image(stream_url, img_path, prefer_ffmpeg=False):
    if prefer_ffmpeg:
        return capture_image_av(stream_url, img_path)
    try:
        return capture_image_cv2(stream_url, img_path)
    except ImportError:
        return capture_image_av(stream_url, img_path)

# AUTH ====================


def get_auth_header_fn(headers):
    auth_header = headers['www-authenticate']
    method, params = auth_header.split(None, 1)
    if method == 'Basic':
        return get_basic_auth_header
    elif method == 'Digest':
        from functools import partial
        parts = _parse_digest_header(params)
        return partial(get_digest_auth_header, parts)


def get_basic_auth_header(_, __, username, password):
    from base64 import b64encode
    b64 = b64encode(('%s:%s' % (username, password)).encode('ascii'))
    return {'Authorization': 'Basic %s' % b64.decode()}


def get_digest_auth_header(parts, rtsp_method, url, username, password):
    realm = parts.get('realm')
    nonce = parts.get('nonce')

    hash_digest = _get_hasher(parts.get('algorithm', 'MD5').upper())

    A1 = '%s:%s:%s' % (username, realm, password)
    A2 = '%s:%s' % (rtsp_method, url)

    HA1 = hash_digest(A1)
    HA2 = hash_digest(A2)

    A3 = '%s:%s:%s' % (HA1, nonce, HA2)

    response = hash_digest(A3)

    return {
        'Authorization': (
            'Digest '
            'username="%s", '
            'realm="%s", '
            'nonce="%s", '
            'uri="%s", '
            'response="%s"'
        ) % (username, realm, nonce, url, response)
    }


def _parse_digest_header(header):
    from urllib.request import parse_http_list

    fields = {}

    for field in parse_http_list(header):
        k, v = field.split('=', 1)
        v = v.strip().strip('"')
        fields[k.lower()] = v

    return fields


def _get_hasher(method='MD5'):
    from hashlib import md5, sha1, sha256, sha512

    hasher = {
        'MD5': md5,
        'SHA': sha1,
        'SHA-256': sha256,
        'SHA-512': sha512
    }.get(method)

    return lambda x: hasher(x.encode('ascii')).hexdigest()
