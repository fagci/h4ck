#!/usr/bin/env python
"""Scan web application for CMS, used techs, vulns"""
import sys

import colorama
from fire import Fire
import requests

from lib.http import iri_to_uri
from lib.progress import Progress

BANNER = r"""
__      _____| |__  _ __ ___   __ _ _ __
\ \ /\ / / _ \ '_ \| '_ ` _ \ / _` | '_ \
 \ V  V /  __/ |_) | | | | | | (_| | |_) |
  \_/\_/ \___|_.__/|_| |_| |_|\__,_| .__/
                                   |_|"""

# file, allow_html

FUZZ_FILES = [
    ('data/web_fuzz.txt', False),
    ('data/web_dir_fuzz.txt', True),
]

with open('data/web_headers.txt') as f:
    HEADER_LIST = [p.rstrip() for p in f]

with open('data/web_cms.txt') as f:
    CMS_LIST = [p.rstrip() for p in f]

with open('data/web_tech.txt') as f:
    TECH_LIST = [p.rstrip() for p in f]

CF = colorama.Fore
CRED = CF.RED
CGREEN = CF.GREEN
CYELLOW = CF.YELLOW
CGREY = CF.WHITE
CDGREY = CF.LIGHTBLACK_EX
CEND = CF.RESET


def check_path(allow_html: bool, url: str):
    try:
        r = requests.get(url, timeout=5, allow_redirects=False, verify=False)
        if not allow_html and r.headers.get('Content-Type') == 'text/html':
            return None
        return url if r.status_code == 200 else None
    except KeyboardInterrupt:
        raise


def check_src(html, inclusions):
    for item in inclusions:
        if item in html:
            yield item


def interruptable(fn):
    def wrap(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except KeyboardInterrupt:
            print('\n[i] Interrupted by user. Exiting.')
            sys.exit(130)
    wrap.__doc__ = fn.__doc__
    return wrap


@interruptable
def check_headers(_, r):
    """Check headers"""
    h = r.headers
    vulns = {
        'csp': not h.get('Content-Security-Policy', False),
        'mitm': not h.get('Strict-Transport-Security', False),
        'xct': 'nosniff' not in h.get('X-Content-Type-Options', ''),
        'xframe': not h.get('X-Frame-Options', False),
        'xss': not h.get('X-XSS-Protection', False),
    }
    vulns = list(filter(lambda v: v[1], vulns.items()))

    for hk, hv in h.items():
        if hk in HEADER_LIST:
            print(f'{CYELLOW}{hk}: {hv}{CEND}')

    if vulns:
        print(f'{CDGREY}[i] Client side vulns:')
        print(f'{", ".join(v[0] for v in vulns)}{CEND}')
    else:
        print(f'{CDGREY}[i] No client side vulns{CEND}')


@interruptable
def check_cms(_, r):
    """Check CMS"""
    cmses = list(check_src(r.text, CMS_LIST))
    if cmses:
        print(f'{CYELLOW}{", ".join(c for c in cmses)}{CEND}')
    else:
        print(f'{CGREY}[-] No CMS found in source{CEND}')


@interruptable
def check_techs(_, r):
    """Check techs"""
    techs = list(check_src(r.text, TECH_LIST))
    if techs:
        print(f'{CYELLOW}{", ".join(t for t in techs)}{CEND}')
    else:
        print(f'{CGREY}[-] No tech found{CEND}')


@interruptable
def check_vulns(url, _):
    """Check vulns"""
    from functools import partial
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as ex:
        urlen = len(url) + 1
        for file, allow_html in FUZZ_FILES:
            print(f'[*] Fuzz {file}...')
            with open(file) as f:
                progress = Progress(sum(1 for _ in f))
                f.seek(0)
                ff = (f'{url}/{ln.rstrip()}' for ln in f)
                check = partial(check_path, allow_html)
                for rurl in ex.map(check, ff):
                    if rurl:
                        print(f'\r{CGREEN}[+] {rurl[urlen:]}{CEND}')
                    progress()


def main(url):
    print('='*42)
    print(BANNER.strip())
    print(f'Target: {url}')
    print('='*42)

    tasks = [
        check_headers,
        check_cms,
        check_techs,
        check_vulns,
    ]

    url = iri_to_uri(url)

    initial_response = requests.get(url, timeout=5, verify=False)

    for task in tasks:
        print(f'\n{task.__doc__}')
        task(url, initial_response)


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    Fire(main)
