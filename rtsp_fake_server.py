#!/usr/bin/env python3
from socketserver import BaseRequestHandler, ThreadingTCPServer
from fire import Fire
from lib.files import LOCAL_DIR


class TCPHandler(BaseRequestHandler):
    def handle(self):
        client_ip = self.client_address

        while True:
            try:
                data = self.request.recv(1024).decode().strip()
                resp = (
                    'RTSP/1.0 %s %s\r\n'
                    'CSeq: %s\r\n'
                    '%s'
                    '\r\n'
                )

                lines = data.splitlines()
                if not lines:
                    return

                method, path, proto = lines[0].split(None, 2)

                if not proto.startswith('RTSP'):
                    print('Bad proto', proto)
                    return

                with (LOCAL_DIR / 'rtsp_honey.log').open('a') as f:
                    f.write('%s %s\n' % (client_ip, path))

                cseq = 1

                if lines[1].startswith('CSeq:'):
                    _, cseq = lines[1].split(None, 1)

                if method == 'OPTIONS':
                    resp = resp % (
                        200, 'OK',
                        cseq,
                        'Public: DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE\r\n',
                    )
                else:
                    resp = resp % (404, 'Not found', cseq, '')

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
