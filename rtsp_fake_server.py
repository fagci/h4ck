#!/usr/bin/env python3
"""Serve RTSP dummy on 554 by default, log paths to file"""
from socketserver import BaseRequestHandler, ThreadingTCPServer

from fire import Fire

from lib.files import LOCAL_DIR

LOG_FILE = LOCAL_DIR / 'rtsp_honey.log'


RESP_TPL = (
    'RTSP/1.0 %s %s\r\n'
    'CSeq: %s\r\n'
    '%s'
    '\r\n'
)

OPTIONS_LINE = 'Public: DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE\r\n'


class TCPHandler(BaseRequestHandler):
    def handle(self):
        client_ip, _ = self.client_address

        while True:
            try:
                data = self.request.recv(1024).decode().strip()

                lines = data.splitlines()
                if not lines:
                    return

                method, path, proto = lines[0].split(None, 2)

                if not proto.startswith('RTSP'):
                    print('Bad proto', proto)
                    return

                with LOG_FILE.open('a') as f:
                    f.write('%s %s\n' % (client_ip, path))

                cseq = 1

                if lines[1].startswith('CSeq:'):
                    _, cseq = lines[1].split(None, 1)

                if method == 'OPTIONS':
                    resp = RESP_TPL % (200, 'OK', cseq, OPTIONS_LINE)
                else:
                    resp = RESP_TPL % (404, 'Not found', cseq, '')

                self.request.sendall(resp.encode())

            except KeyboardInterrupt:
                self.server.shutdown()
                break

            except:
                self.finish()
                break


def main(H='0.0.0.0', P=554):
    with ThreadingTCPServer((H, P), TCPHandler) as srv:
        srv.serve_forever()


if __name__ == "__main__":
    Fire(main)
