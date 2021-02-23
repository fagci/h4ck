#!/usr/bin/env python
import os
from pathlib import Path
import re
from socket import SocketIO, create_connection
from time import sleep
from fire import Fire

connections = dict()
header_re = re.compile(r'RTSP/\d\.\d (\d\d\d)')


def query(host, port=554, path='', cred=''):
    connection: SocketIO = connections.get(f'{host}:{port}')
    if not connection:
        return 500

    url = get_url(host, port, path, cred)

    request = (
        f'DESCRIBE {url} RTSP/1.0\r\n'
        'CSeq: 2\r\n'
        '\r\n'
    )

    try:
        connection.sendall(request.encode())
        response = connection.read(512)
        header_matches = header_re.findall(response)
        if header_matches:
            return int(header_matches[0])


def get_url(host, port=554, path='', cred=''):
    if cred:
        cred = f'{cred}@'
    return f'rtsp://{cred}{host}:{port}{path}'


def main(H='', P='', C='', t=3):
    work_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    data_dir = work_dir / 'data'
    local_dir = work_dir / 'local'

    hosts_file = H or local_dir / 'hosts_554.txt'
    paths_file = P or data_dir / 'rtsp_paths4.txt'
    creds_file = C or data_dir / 'rtsp_creds.txt'

    paths = (ln.rstrip() for ln in open(paths_file))
    creds = (ln.rstrip() for ln in open(creds_file))

    with open(hosts_file) as hf:
        for ln in hf:
            host = ln.rstrip()
            port = 554

            if ':' in host:
                host, port = host.split(':')

            # show must go on
            retries = 3
            connection: SocketIO = None
            while retries:
                try:
                    connection = create_connection((host, int(port)))
                    connections[f'{host}:{port}'] = connection
                    break
                except:
                    sleep(1.5/retries)
                    retries -= 1
                    continue

            if not connection:
                continue # next host

            for path in paths:

                for cred in creds:

                    c_url = get_url(host, port, path, cred)
                    print(c_url)


if __name__ == "__main__":
    Fire(main)
