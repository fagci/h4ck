#!/usr/bin/env python3
import asyncio
from functools import partial
from pathlib import Path
from time import time

from fire import Fire

from lib.net import RTSPConnection
from lib.scan import generate_ips, process_threaded_async

counter = 0
max_count = 1024


def check(out, p, t, i, ip):
    global counter

    if counter >= max_count:
        raise StopIteration()

    tt = time()
    with RTSPConnection(ip, p, i, t) as connection:
        dt = time() - tt
        response = connection.query()

        if not response.found or 'PLAY' not in response.headers.get('public', ''):
            return

        server = response.headers.get('server', '-')

        if counter < max_count:  # precision ensurance
            counter += 1
            print('{:<4} {:<15} ({:>4} ms) {}'.format(
                counter, ip, int(dt*1000), server[:20]), flush=True)
            out.write('%s\n' % ip)


async def check_ips(p: int = 554, c: int = 1024, l: int = 2000000, w: int = 1500, t=1.5, f=False, F=False, i=None):
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
            ch = partial(check, out, p, t, i)
            await process_threaded_async(ch, ips, w)
    except KeyboardInterrupt:
        print('Interrupted by user.')

def main(p: int = 554, c: int = 1024, l: int = 2000000, w: int = 1500, t=1.5, f=False, F=False, i=None):
    asyncio.run(check_ips(p,c,l,w,t,f,F,i))

if __name__ == "__main__":
    Fire(main)
