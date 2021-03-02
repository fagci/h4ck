import logging
from socket import SOL_SOCKET, SO_BINDTODEVICE, create_connection, socket
from socket import timeout as SocketTimeout
from time import sleep, time
from typing import Optional

logger = logging.getLogger('lib.connection')
logger.setLevel(logging.CRITICAL)


class Packet:
    """Base class for communication"""
    protocol: str = ''
    headers: dict[str, str] = {}
    body: str = ''


class Response(Packet):
    """Response packet"""
    code: int = 999
    status_msg: str = ''

    def __init__(self, data: str = ''):
        """Create response, parse data string if passed.

        :param str data: response string from server"""

        if not data:
            return

        data_lines = iter(data.splitlines())

        self.protocol, code, self.status_msg = next(data_lines).split(None, 2)
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
    method: str
    url: str

    PROTO_RTSP_1 = 'RTSP/1.0'
    PROTO_HTTP_1 = 'HTTP/1.0'
    PROTO_HTTP_1_1 = 'HTTP/1.1'

    def __init__(self, method: str = 'OPTIONS', url: str = '*', protocol: str = ''):
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
    _c: Optional[socket] = None
    user_agent = 'Mozilla/5.0'

    def __init__(self, host, port, interface: str = '', timeout: float = 3, query_timeout: float = 5):
        self.host = host
        self.port = port
        self.interface = interface
        self._connection_timeout = timeout
        self._query_timeout = query_timeout

    def __enter__(self):

        start = time()
        address = (self.host, self.port)

        while time() - start < 3:
            try:
                self._c = create_connection(address, self._connection_timeout)
                self._c.settimeout(self._query_timeout)
                if self.interface:
                    self._c.setsockopt(SOL_SOCKET, SO_BINDTODEVICE,
                                       self.interface.encode())
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

        req = (
            'GET %s HTTP/1.1\r\n'
            'Host: %s\r\n'
            'User-Agent: %s\r\n'
            '\r\n\r\n'
        ) % (url, self.host, self.user_agent)

        try:
            connection.sendall(req.encode())
            # TODO: get overall response
            data = connection.recv(1024).decode()
            if data.startswith('HTTP/'):
                return Response(data)
        except OSError:
            pass

        return Response()


class RTSPConnection(Connection):
    M_OPTIONS = 'OPTIONS'
    M_DESCRIBE = 'DESCRIBE'

    _cseqs = dict()

    def query(self, url: str = '*', headers: dict = {}) -> Response:
        method = self.M_OPTIONS if url == '*' else self.M_DESCRIBE
        connection = self._c

        if url == '*':
            cseq = 0
        else:
            cseq = self._cseqs.get(connection, 0)

        cseq += 1

        self._cseqs[connection] = cseq

        headers['CSeq'] = cseq
        headers['User-Agent'] = 'Mozilla/5.0'
        headers['Accept'] = 'application/sdp'

        request = Request(method, url, Request.PROTO_RTSP_1)
        request.headers = headers

        logger.info('\n<< %s' % str(request).rstrip())

        try:
            connection.sendall(str(request).encode())
            data = connection.recv(1024).decode()

            logger.info('\n>> %s' % data.rstrip())

            if data.startswith('RTSP/'):
                response = Response(data)

                if response.code == 401:
                    self._auth_fn = self.get_auth_header_fn(response.headers)

                return response

        except BrokenPipeError as e:
            logger.error(repr(e))
        except SocketTimeout as e:
            logger.warning(repr(e))
        except ConnectionResetError as e:
            logger.error(repr(e))
        except UnicodeDecodeError as e:
            logger.error(repr(e))

        return Response()

    def get(self, path):
        url = self.url(path)
        return self.query(url)

    def auth(self, path, cred):
        url = self.url(path)
        logger.info('Auth %s %s' % (url, cred))
        auth_headers = self._auth_fn(self.M_DESCRIBE, url, *cred.split(':'))
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
