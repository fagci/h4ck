#!/usr/bin/env -S python -u
from pathlib import Path

from fire import Fire

from lib.scan import check_port, generate_ips, process_each

__author__ = 'Mikhail Yudin aka fagci'

counter = 0


def check(ip, pl, out, max_count, *scanopts):
    global counter

    with pl:
        if counter >= max_count:
            raise StopIteration()

    res = check_port(ip, *scanopts)

    if res:
        _, time = res

        with pl:
            if counter < max_count:  # precision ensurance
                counter += 1
                print(f'{counter:<4} {ip:<15} {int(time*1000):>4} ms')
                out.write(f'{ip}\n')


def check_ips(p: int, c: int = 1024, l: int = 2_000_000, w: int = 1500, t=1.5, f=False, F=False, d=False, i=None):
    """Scan random ips for port

    :param int p: port to check
    :param int c: needed ips count
    :param int l: maximum processing IPs
    :param int w: workers count
    :param float t: connect timeout
    :param bool f: overwrite result file w/prompt
    :param bool F: force overwrite result file
    :param bool d: double check each host
    :param bool i: network interface to use"""

    results_file = Path(f'./local/hosts_{p}.txt')

    if F:
        f = True
    elif f:
        f = input(f'Delete hosts_{p}.txt? y/n: ').lower() == 'y'

    ips = generate_ips(l)

    try:
        with open(results_file, 'w' if f else 'a') as out:
            process_each(check, ips, w, out, c, p, t, d, i)
    except KeyboardInterrupt:
        print('Interrupted by user.')


if __name__ == "__main__":
    Fire(check_ips)
