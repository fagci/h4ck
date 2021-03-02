from lib.net import Response

r = Response((
    'RTSP/1.0 401 Unauthorized\r\n'
    'CSeq: 1\r\n'
    'Session:        645252166;timeout=60\r\n'
    'WWW-Authenticate: Digest realm="4419b63f5e51", nonce="8b84a3b789283a8bea8da7fa7d41f08b", stale="FALSE"\r\n'
    'WWW-Authenticate: Basic realm="4419b63f5e51"\r\n'
    'Date:  Sat, Aug 16 2014 02:22:28 GMT\r\n\r\n'
    'some data\r\n\r\n'
))

print(r)
