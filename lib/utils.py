def interruptable(fn):
    """Decorator to handle exit with Ctrl+C"""
    import sys

    def wrap(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except KeyboardInterrupt:
            print('\n[i] Interrupted by user. Exiting.')
            sys.exit(130)
    wrap.__doc__ = fn.__doc__
    return wrap


def tmof_retry(fn):
    """Decorator to deal with OSError 24: too many open files"""
    def wrap(*args, **kwargs):
        while True:
            try:
                return fn(*args, **kwargs)
            except OSError as e:
                if e.errno == 24:
                    from time import sleep
                    sleep(0.15)
                    continue
                raise
    wrap.__doc__ = fn.__doc__
    return wrap


def tim():
    from datetime import datetime
    return datetime.now().strftime('%H:%M:%S')


def dt():
    from datetime import datetime
    return datetime.now().strftime('%d.%m %H:%M:%S')


def str_to_filename(text):
    from re import sub
    return sub(r'[^A-Za-z0-9.-]+', '_', text)


def parse_range_list(rgstr):
    """Parse ranges such as 2-5,7,12,8-11 to [2,3,4,5,7,8,9,10,11,12]"""
    import re
    from itertools import chain

    def parse_range(rg):
        if len(rg) == 0:
            return []
        parts = re.split(r'[:-]', rg)
        if len(parts) > 2:
            raise ValueError("Invalid range: {}".format(rg))
        try:
            return range(int(parts[0]), int(parts[-1])+1)
        except ValueError:
            if len(parts) == 1:
                return parts
            else:
                raise ValueError("Non-integer range: {}".format(rg))
    rg = map(parse_range, re.split(r'\s*[,;]\s*', rgstr))
    return list(set(chain.from_iterable(rg)))


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def random_lowercase_alpha(min_length: int = 3, max_length: int = 16):
    from random import randrange
    return ''.join(
        chr(
            randrange(ord('a'), ord('z'))
        ) for _ in range(
            randrange(min_length, max_length)
        )
    )


def geoip_str_online(ip):
    import requests
    url = 'https://ipinfo.io/%s/json' % ip
    try:
        d = requests.get(url).json()
        if d:
            return '%s, %s, %s' % (d.get("country"), d.get("region"), d.get("city"))
    except:
        pass
    return ''


def encode_ip(ip, password):
    if '.' in ip:
        char = '-'
        parts = ip.split('.')
    else:
        char = '.'
        parts = ip.split('-')
    return char.join([str(int(x) ^ ord(password[i]))
                      for i, x in enumerate(parts)])


def sh(*args):
    import subprocess
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()
    return stdout


def ip4_to_int(ip: str):
    from ipaddress import IPv4Address
    return int(IPv4Address(ip))


def int_to_ip4(num: int):
    from ipaddress import IPv4Address
    return str(IPv4Address(num))
