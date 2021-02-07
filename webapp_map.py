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

FUZZ_FILES = [
    'data/web_fuzz.txt',
    'data/web_dir_fuzz.txt',
]

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
        sys.exit(e.errno)


def check_path(url):
    try:
        with urlopen(url, timeout=5) as u:
            return url if u.getcode() == 200 else None
    except KeyboardInterrupt:
        raise
    except:
        pass


def check_src(url, inclusions):
    try:
        with urlopen(url, timeout=5) as u:
            charset = u.info().get_content_charset()
            html = u.read().decode(charset or 'utf-8', errors='ignore').lower()
            for item in inclusions:
                if item in html:
                    yield item
    except (URLError, HTTPError) as e:
        print(f'{CRED}[!!] {e}{CEND}')
        sys.exit(e.errno)


class Progress:
    prg = '|/-\\'
    prg_len = len(prg)

    def __init__(self, total=0):
        self.i = 0
        self.total = total
        self.val = ''
        self.update = self._progress if total else self._spin

    def _spin(self):
        self.i %= self.prg_len
        self.val = self.prg[self.i]

    def _progress(self):
        self.val = f'{int(self.i*100/self.total)}%'

    def __call__(self):
        self.i += 1
        self.update()
        print(f'\r    \r{self.val}', end='', flush=True)
        if self.total != 0 and self.total == self.i:
            self.__del__()

    def __del__(self):
        print('\r    \r', end='', flush=True)


def interruptable(fn):
    def wrap(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except KeyboardInterrupt:
            print('\n  [i] Interrupted by user. Exiting.\n')
            sys.exit(130)
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
        print(f'{CYELLOW}  {hk}: {hv}{CEND}')

    if vulns:
        print(f'\n{CGREEN}  [i] Client side vulns:{CEND}')
        print(f'{CYELLOW}  {", ".join(v[0] for v in vulns)}{CEND}')
    else:
        print(f'\n{CDGREY}  [i] No client side vulns{CEND}')


@interruptable
def check_cms(url):
    """Check CMS"""
    cmses = list(check_src(url, CMS_LIST))
    if cmses:
        print(f'{CYELLOW}  {", ".join(c for c in cmses)}{CEND}')
    else:
        print(f'{CGREY}  [i] No CMS found in source{CEND}')


@interruptable
def check_techs(url):
    """Check techs"""
    techs = list(check_src(url, TECH_LIST))
    if techs:
        print(f'{CYELLOW}  {", ".join(t for t in techs)}{CEND}')
    else:
        print(f'{CGREY}  [i] No tech found{CEND}')


@interruptable
def check_vulns(url):
    """Check vulns"""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as ex:
        urlen = len(url) + 1
        for file in FUZZ_FILES:
            print(f'\n  [*] Fuzz {file}...\n')
            with open(file) as f:
                progress = Progress(sum(1 for _ in f))
                f.seek(0)
                ff = (f'{url}/{ln.rstrip()}' for ln in f)
                for rurl in ex.map(check_path, ff):
                    if rurl:
                        print(f'\r{CGREEN}  [+] {rurl[urlen:]}{CEND}')
                    progress()


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
    print(f'Map web app: {url}')
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
