#!/usr/bin/env python3
from pathlib import Path
from time import time

from fire import Fire

from lib.scan import generate_ips, process_each
from lib.net import RTSPConnection
from lib.models import add_result

counter = 0
max_count = 1024


def check(ip, pl, out, p, t, i):
    global counter

    with pl:
        if counter >= max_count:
            raise StopIteration()

    tt = time()
    with RTSPConnection(ip, p, i, t) as connection:
        dt = time() - tt
        response = connection.query()

        if not response.found or 'PLAY' not in response.headers.get('public'):
            return

        server = response.headers.get('server', '-')

        with pl:
            if counter < max_count:  # precision ensurance
                counter += 1
                print('{:<4} {:<15} ({:>4} ms) {}'.format(
                    counter, ip, int(dt*1000), server[:20]))
                add_result(ip, p, server, ['fortune'],
                           response.headers_str, time=int(dt*1000))
                out.write('%s\n' % ip)


def check_ips(p: int = 554, c: int = 1024, l: int = 2000000, w: int = 1500, t=1.5, f=False, F=False, i=None):
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

    results_file = Path('./local/rtsp_%d.txt' % p)

    if F:
        f = True
    elif f:
        f = input('Delete hosts_%d.txt? y/n: ' % p).lower() == 'y'

    ips = generate_ips(l)

    try:
        with open(results_file, 'w' if f else 'a') as out:
            process_each(check, ips, w, out, p, t, i)
    except KeyboardInterrupt:
        print('Interrupted by user.')


if __name__ == "__main__":
    Fire(check_ips)
