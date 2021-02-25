#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
from socket import SOL_SOCKET, SO_BINDTODEVICE, SocketIO, create_connection, setdefaulttimeout, timeout
from time import sleep, time

from fire import Fire
from tqdm import tqdm


fake_path = '/f4k3p4th'

work_dir = Path(os.path.dirname(os.path.abspath(__file__)))

data_dir = work_dir / 'data'
local_dir = work_dir / 'local'

paths_file = data_dir / 'rtsp_paths.txt'
creds_file = data_dir / 'rtsp_creds.txt'

paths = [fake_path] + [ln.rstrip() for ln in open(paths_file)]
creds = [ln.rstrip() for ln in open(creds_file)]


def query(connection, url):
    request = (
        f'DESCRIBE {url} RTSP/1.0\r\n'
        'CSeq: 2\r\n'
        '\r\n'
    )

    try:
        connection.sendall(request.encode())
        response = connection.recv(1024).decode()
        if response.startswith('RTSP/'):
            _, code, msg = response.split(None, 2)
            code = int(code)
            if code == 401 and 'digest' in response.lower():
                return 500  # lazy to implement for now
            return code
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
    start = time()

    while time() - start < 10:
        try:
            c = create_connection((host, int(port)), 3)
            if interface:
                c.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, interface.encode())
            return c
        except KeyboardInterrupt:
            raise
        except OSError:
            sleep(1)
        except:
            return


def process_target(target_params):
    host, port, single_path, interface = target_params
    connection = connect(host, port, interface)

    results = []

    if not connection:
        return results  # next host

    for path in paths:
        url = get_url(host, port, path)
        code = query(connection, url)

        if code >= 500:
            connection.close()
            return results  # first request fail, cant continue

        if (not 200 <= code < 300) and code not in [401, 403]:
            continue

        if path == fake_path:
            break

        if 200 <= code < 300:
            results.append(url)
            if single_path:
                connection.close()
                return results
            continue

        for cred in creds:
            url = get_url(host, port, path, cred)
            code = query(connection, url)
            if code >= 500:
                connection.close()
                return results  # something goes wrong =(

            if not 200 <= code < 300:
                continue  # access denied

            results.append(url)
            if single_path:
                connection.close()
                return results
            break  # one cred per path is enough

    connection.close()
    return results


def main(H='', w=None, sp=False, i=''):
    hosts_file = H or local_dir / 'hosts_554.txt'

    setdefaulttimeout(3)

    with ThreadPoolExecutor(w) as ex:
        with open(hosts_file) as hf:
            futures = {}

            for ln in hf:
                host = ln.rstrip()
                port = 554

                if ':' in host:
                    host, port = host.split(':')

                arg = (host, port, sp, i)

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
