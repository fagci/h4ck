#!/usr/bin/env -S python -u
from pathlib import Path
from socket import SOL_SOCKET, SO_BINDTODEVICE, create_connection
from time import time, sleep

from fire import Fire

from lib.scan import generate_ips, process_each

counter = 0
max_count = 1024

REQ = b'OPTIONS * RTSP/1.0\r\nCSeq: 1\r\n\r\n'


def check(ip, pl, out, p, t, i):
    global counter

    with pl:
        if counter >= max_count:
            raise StopIteration()

    start = time()
    code = 500
    response = ''

    while time() - start < t*2.5:
        try:
            c = create_connection((ip, int(p)), t)
            if i:
                c.setsockopt(SOL_SOCKET, SO_BINDTODEVICE, i.encode())
            c.sendall(REQ)
            response = c.recv(1024).decode()
            if response.startswith('RTSP/'):
                _, code, msg = response.split(None, 2)
            break
        except KeyboardInterrupt:
            raise
        except OSError:
            sleep(1)
        except:
            return

    if int(code) == 200:
        server = ''
        for h in response.splitlines()[1:]:
            if h.startswith('Server'):
                _, server = h.split(None, 1)
                server = server.strip()
                break
        with pl:
            if counter < max_count:  # precision ensurance
                counter += 1
                print(f'{counter:<4} {ip:<15} {server[:20]}')
                out.write(f'{ip}\n')


def check_ips(p: int, c: int = 1024, l: int = 2_000_000, w: int = 1500, t=1.5, f=False, F=False, i=None):
    """Scan random ips for port

    :param int p: port to check
    :param int c: needed ips count
    :param int l: maximum processing IPs
    :param int w: workers count
    :param float t: connect timeout
    :param bool f: overwrite result file w/prompt
    :param bool F: force overwrite result file
    :param bool i: network interface to use"""
    global max_count

    max_count = c

    results_file = Path(f'./local/rtsp_{p}.txt')

    if F:
        f = True
    elif f:
        f = input(f'Delete hosts_{p}.txt? y/n: ').lower() == 'y'

    ips = generate_ips(l)

    try:
        with open(results_file, 'w' if f else 'a') as out:
            process_each(check, ips, w, out, p, t, i)
    except KeyboardInterrupt:
        print('Interrupted by user.')


if __name__ == "__main__":
    Fire(check_ips)
