import logging
from socket import SOL_SOCKET, SO_BINDTODEVICE, create_connection, socket
from socket import timeout as SocketTimeout
from time import sleep, time
from typing import Optional

from lib.files import LOCAL_DIR

UA_FILE_PATH = LOCAL_DIR / '.useragent'

local_ua = None

if UA_FILE_PATH.exists():
    with UA_FILE_PATH.open() as f:
        local_ua = f.readline().strip()

DEFAULT_UA = local_ua or 'Mozilla/5.0'

M_OPTIONS = 'OPTIONS'
M_DESCRIBE = 'DESCRIBE'

PROTO_RTSP_1 = 'RTSP/1.0'
PROTO_HTTP_1 = 'HTTP/1.0'
PROTO_HTTP_1_1 = 'HTTP/1.1'

logger = logging.getLogger('lib.connection')
logger.setLevel(logging.CRITICAL)


class Packet:
    """Base class for communication"""
    __slots__ = ('protocol', 'headers', 'body')

    def __init__(self):
        self.protocol: str = ''
        self.headers: dict[str, str] = {}
        self.body: str = ''


class Response(Packet):
    """Response packet"""
    __slots__ = ('code', 'status_msg')

    def __init__(self, data: str = ''):
        """Create response, parse data string if passed.

        :param str data: response string from server"""
        super().__init__()
        self.code: int = 999
        self.status_msg: str = ''

        if not data:
            return

        data_lines = iter(data.splitlines())

        r_parts = next(data_lines).split(None, 2)
        if len(r_parts) == 3:
            self.protocol, code, self.status_msg = r_parts
        else:
            self.protocol, code = r_parts

        self.code = int(code)

        for ln in data_lines:
            if ln:
                if ':' in ln:
                    k, v = ln.split(':', 1)
                    self.headers[k.strip().lower()] = v.strip()
                continue
            break

        self.body = '\n'.join(data_lines)

    @property
    def internal_error(self):
        return self.code == 999

    @property
    def error(self):
        return self.code >= 500

    @property
    def not_found(self):
        return self.code == 404

    @property
    def ok(self):
        return self.code == 200

    @property
    def found(self):
        return 200 <= self.code < 300

    @property
    def auth_needed(self):
        return self.code == 401

    @property
    def headers_str(self):
        return '\n'.join('%s: %s' % v for v in self.headers.items())

    def __repr__(self):
        return (
            'Proto: %s\n'
            'Code: %d\n'
            'Status msg: %s\n'
            'Headers: %s\n'
            'Body: %s'
        ) % (self.protocol, self.code, self.status_msg, self.headers, self.body)


class Request(Packet):
    """Used to build request string"""
    __slots__ = ('method', 'url')

    def __init__(self, method: str = M_OPTIONS, url: str = '*', protocol: str = ''):
        super().__init__()
        self.method = method
        self.url = url
        self.protocol = protocol

    def __repr__(self) -> str:
        headers_str = '\r\n'.join('%s: %s' % v for v in self.headers.items())

        if headers_str:
            headers_str += '\r\n'

        body = self.body

        if body:
            body += '\r\n\r\n'

        return (
            '%s %s %s\r\n'
            '%s'
            '\r\n'
            '%s'
        ) % (
            self.method, self.url, self.protocol,
            headers_str,
            body
        )


class Connection:
    __slots__ = ('_host', '_port', '_iface', '_connection_timeout',
                 '_query_timeout', '_user_agent', '_c')

    def __init__(self, host, port, interface: str = '', timeout: float = 3, query_timeout: float = 5, ua: str = DEFAULT_UA):
        self._host = host
        self._port = port
        self._iface = interface
        self._connection_timeout = timeout
        self._query_timeout = query_timeout
        self._c: Optional[socket] = None
        self._user_agent = ua

    def query(self, url='*'):
        raise NotImplementedError

    def get(self, path):
        raise NotImplementedError

    def auth(self, path, cred):
        raise NotImplementedError

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    def __enter__(self):

        start = time()
        address = (self.host, self.port)

        while time() - start < 3:
            try:
                self._c = create_connection(address, self._connection_timeout)
                self._c.settimeout(self._query_timeout)
                if self._iface:
                    _if = self._iface.encode()
                    self._c.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, _if)
                break
            except KeyboardInterrupt:
                raise
            except SocketTimeout:
                break
            except OSError:
                sleep(1)

        return self

    def __exit__(self, _type, value, _trace):
        if self._c:
            self._c.close()
        is_interrupt = isinstance(value, KeyboardInterrupt)
        if value:
            logger.warn('%s %s' % (_type, value))
        return not is_interrupt


class HTTPConnection(Connection):
    def get(self, url):
        connection = self._c
        if not connection:
            return Response()

        request = Request('GET', url, PROTO_HTTP_1_1)
        request.headers['Host'] = self.host
        request.headers['User-Agent'] = self._user_agent

        try:
            connection.sendall(str(request).encode())
            maxlen = 1024 * 1024 * 128
            data_bytes = b''
            while True:
                d = connection.recv(1024)
                if not d or len(data_bytes) > maxlen:
                    break
                data_bytes += d
            data = data_bytes.decode(errors='ignore')
            if data.startswith('HTTP/'):
                return Response(data)
        except OSError:
            pass

        return Response()


class RTSPConnection(Connection):
    __slots__ = ('cseq', '_auth_fn')

    def __init__(self, host, port=554, interface: str = '', timeout: float = 2, query_timeout: float = 5, ua: str = DEFAULT_UA):
        super().__init__(host, port, interface=interface,
                         timeout=timeout, query_timeout=query_timeout, ua=ua)
        self.cseq = 0

    def query(self, url: str = '*', headers: dict = {}) -> Response:
        method = M_OPTIONS if url == '*' else M_DESCRIBE
        connection = self._c
        if not connection:
            return Response()

        if url == '*':
            self.cseq = 0

        self.cseq += 1

        headers['CSeq'] = self.cseq
        headers['User-Agent'] = self._user_agent
        headers['Accept'] = 'application/sdp'

        request = Request(method, url, PROTO_RTSP_1)
        request.headers = headers
        request_str = str(request)

        logger.info('<< %s' % request_str.rstrip())

        err = 'Unhandled error'

        try:
            connection.sendall(request_str.encode('ascii'))
            data_bytes = connection.recv(1024)

            if data_bytes:
                data = data_bytes.decode(errors='replace')

                logger.info('>> %s' % data.rstrip())

                if data.startswith('RTSP/'):
                    response = Response(data)

                    if response.code == 401:
                        self._auth_fn = self.get_auth_header_fn(
                            response.headers)

                    return response
                else:
                    err = 'Not rtsp response'
            else:
                err = 'Empty response'

        except BrokenPipeError as e:
            logger.error(repr(e))
            err = e
        except SocketTimeout as e:
            logger.warning(repr(e))
            err = e
        except ConnectionResetError as e:
            logger.error(repr(e))
            err = e
        except UnicodeDecodeError as e:
            logger.error(repr(e))
            err = e
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(repr(e))
            err = e

        response = Response()
        response.status_msg = str(err)
        return response

    def get(self, path):
        url = self.url(path)
        return self.query(url)

    def auth(self, path, cred):
        url = self.url(path)
        logger.info('Auth %s %s' % (url, cred))
        auth_headers = self._auth_fn(M_DESCRIBE, url, *cred.split(':'))
        return self.query(url, auth_headers)

    def url(self, path: str = '', cred: str = '') -> str:
        if cred:
            cred = '%s@' % cred
        return 'rtsp://%s%s:%d%s' % (cred, self.host, self.port, path)

    @staticmethod
    def get_auth_header_fn(headers):
        auth_header = headers['www-authenticate']
        method, params = auth_header.split(None, 1)

        if method == 'Basic':
            return RTSPConnection.get_basic_auth_header
        elif method == 'Digest':
            from functools import partial
            parts = RTSPConnection._parse_digest_header(params)
            return partial(RTSPConnection.get_digest_auth_header, parts)

    @staticmethod
    def get_basic_auth_header(_, __, username, password):
        from base64 import b64encode
        b64 = b64encode(('%s:%s' % (username, password)).encode('ascii'))
        return {'Authorization': 'Basic %s' % b64.decode()}

    @staticmethod
    def get_digest_auth_header(parts, rtsp_method, url, username, password):
        realm = parts.get('realm')
        nonce = parts.get('nonce')
        algo = parts.get('algorithm', 'MD5').upper()

        hash_digest = RTSPConnection._get_hasher(algo)

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

    @staticmethod
    def _parse_digest_header(header):
        from urllib.request import parse_http_list

        fields = {}

        for field in parse_http_list(header):
            k, v = field.split('=', 1)
            v = v.strip().strip('"')
            fields[k.lower()] = v

        return fields

    @staticmethod
    def _get_hasher(method='MD5'):
        from hashlib import md5, sha1, sha256, sha512

        hasher = {
            'MD5': md5,
            'SHA': sha1,
            'SHA-256': sha256,
            'SHA-512': sha512
        }.get(method)

        return lambda x: hasher(x.encode('ascii')).hexdigest()
