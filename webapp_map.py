#!/usr/bin/env python
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

CRED = '\033[31m'
CGREEN = '\033[32m'
CYELLOW = '\033[33m'
CGREY = '\033[37m'
CDGREY = '\033[90m'
CEND = '\033[0m'

with open('data/web_headers.txt') as f:
    HEADER_LIST = [p.rstrip() for p in f]

with open('data/web_cms.txt') as f:
    CMS_LIST = [p.rstrip() for p in f]

with open('data/web_tech.txt') as f:
    TECH_LIST = [p.rstrip() for p in f]


def get_headers(url):
    try:
        with urlopen(url, timeout=5) as u:
            items = u.info().items()
            return {hk: hv for hk, hv in items if hk in HEADER_LIST}
    except KeyboardInterrupt:
        raise
    except (URLError, HTTPError) as e:
        print(f'{CRED}[!!] {e}{CEND}')
        exit(e.errno)


def check_path(url):
    try:
        with urlopen(url, timeout=3) as u:
            return u.getcode() == 200
    except KeyboardInterrupt:
        raise
    except:
        return False


def check_src(url, inclusions):
    try:
        with urlopen(url, timeout=5) as u:
            html = u.read().decode().lower()
            for item in inclusions:
                if item in html:
                    yield item
    except (URLError, HTTPError) as e:
        print(f'{CRED}[!!] {e}{CEND}')
        exit(e.errno)


def interruptable(fn):
    def wrap(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except KeyboardInterrupt:
            print('[i] Interrupted by user. Exiting.\n')
            exit(130)
    wrap.__doc__ = fn.__doc__
    return wrap


@interruptable
def check_headers(url):
    """Check headers"""
    h = get_headers(url)
    vulns = {
        'csp': not h.get('Content-Security-Policy', False),
        'mitm': not h.get('Strict-Transport-Security', False),
        'xct': 'nosniff' not in h.get('X-Content-Type-Options', ''),
        'xframe': not h.get('X-Frame-Options', False),
        'xss': not h.get('X-XSS-Protection', False),
    }
    vulns = filter(lambda v: v[1], vulns.items())

    for hk, hv in h.items():
        print(f'{CYELLOW}  - {hk}: {hv}{CEND}')

    if vulns:
        print(f'\n{CGREEN}  [i] Client side vulns:{CEND}')
        for v in vulns:
            print(f'{CYELLOW}  - {v[0]}{CEND}')
    else:
        print(f'\n{CDGREY}  [i] No client side vulns{CEND}')


@interruptable
def check_cms(url):
    """Check CMS"""
    cmses = list(check_src(url, CMS_LIST))
    if cmses:
        for c in cmses:
            print(f'{CYELLOW}  - {c}{CEND}')
    else:
        print(f'{CGREY}  [i] No CMS found in source{CEND}')


@interruptable
def check_techs(url):
    """Check techs"""
    techs = list(check_src(url, TECH_LIST))
    if techs:
        for tech in techs:
            print(f'{CYELLOW}  - {tech}{CEND}')
    else:
        print(f'{CGREY}  [i] No tech found{CEND}')


@interruptable
def check_vulns(url):
    """Check vulns"""
    with open('data/web_files.txt') as f:
        for ln in f:
            vp = ln.rstrip()
            if check_path(f'{url}/{vp}'):
                print(f'\n{CGREEN}  [+] {vp}{CEND}')
            else:
                print(f'{CGREY}.{CEND}', end='', flush=True)


def iri_to_uri(iri):
    from urllib.parse import quote, urlsplit, urlunsplit
    parts = urlsplit(iri)
    uri = urlunsplit((
        parts.scheme,
        parts.netloc.encode('idna').decode('ascii'),
        quote(parts.path),
        quote(parts.query, '='),
        quote(parts.fragment),
    ))
    return uri


def main(url):
    print('='*40)
    print(f'Map CMS for {url}')
    print('='*40)

    tasks = [
        check_headers,
        check_cms,
        check_techs,
        check_vulns,
    ]

    url = iri_to_uri(url)

    for task in tasks:
        print(f'\n{CGREY}{task.__doc__}{CEND}\n')
        task(url)


if __name__ == "__main__":
    main(sys.argv[1])
