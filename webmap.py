#!/usr/bin/env python3
"""Scan web application for CMS, used techs, vulns"""

from collections import defaultdict
import re
from urllib.parse import urlparse

from fire import Fire
import requests
from requests.models import Response

from lib.colors import *
from lib.files import DATA_DIR, FUZZ_DIR
from lib.http import iri_to_uri
from lib.progress import Progress
from lib.scan import get_domains_from_cert
from lib.utils import interruptable, tim

BANNER = r"""
%s__      _____| |__  _ __ ___   __ _ _ __
%s\ \ /\ / / _ \ '_ \| '_ ` _ \ / _` | '_ \
%s \ V  V /  __/ |_) | | | | | | (_| | |_) |
%s  \_/\_/ \___|_.__/|_| |_| |_|\__,_| .__/
%s                                   |_|%s""" % (
    CEND,
    CEND,
    CGREY,
    CGREY,
    CDGREY,
    CEND
)

# file, allow_html

FUZZ_FILES = [
    (str(FUZZ_DIR / 'web_fw.txt'), True),
    (str(FUZZ_DIR / 'web.txt'), False),
    (str(FUZZ_DIR / 'web_dir.txt'), True),
]

with (DATA_DIR / 'web_headers.txt').open() as f:
    HEADER_LIST = [p.rstrip() for p in f]

with (DATA_DIR / 'web_cms.txt').open() as f:
    CMS_LIST = [p.rstrip() for p in f]

with (DATA_DIR / 'web_tech.txt').open() as f:
    TECH_LIST = [p.rstrip() for p in f]


session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0'}


@interruptable
def check_path(allow_html: bool, url: str):
    try:
        r = session.get(url, timeout=5, allow_redirects=False,
                        verify=False, stream=True, headers=headers)
        if (
            allow_html or r.headers.get('Content-Type') != 'text/html'
        ) and r.status_code == 200:
            return True, url, len(r.content)
    except requests.ConnectionError as e:
        print(end='\r')
        err(repr(e))
    except:
        pass
    return False, url, 0


def check_src(text: str, inclusions):
    return filter(lambda x: x in text, inclusions)


@interruptable
def check_domains(url, _):
    """Get linked domains"""
    try:
        up = urlparse(url)
        hostname, port = up.hostname, up.port
        port = port if port and port != 80 else 443
        linked_domains = get_domains_from_cert(hostname, port)
        if linked_domains:
            found('Domains:', ', '.join(linked_domains))
        else:
            nfound('No domains found')
    except Exception as e:
        nfound('Failed:', repr(e))


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
            info('%s: %s' % (hk, hv))

    if vulns:
        found('Client side vulns:', ', '.join(v[0] for v in vulns))
    else:
        nfound('No client side vulns')


@interruptable
def check_analytics(_, r: Response):
    """Check analytics"""
    regs = {
        'adsense': r'pub-\d+',
        'google': r'ua-[0-9-]+',
        'googleTagManager': r'gtm-[^&\'"%]+',
        'mail.ru': r'top.mail.ru[^\'"]+from=(\d+)',
        'yandexMetrika': r'metrika.yandex[^\'"]+?id=(\d+)',
        'vk': r'vk-[^&"\'%]+'
    }
    for name, reg in regs.items():
        m = re.findall(reg, r.text, re.IGNORECASE)
        if m:
            found(name, m[0])


@interruptable
def check_social(_, r):
    """Check social"""
    regs = {
        'facebook': r'facebook\.com/([^"\'/]+)',
        'github': r'github\.com/([^"\'/]+)',
        'instagram': r'instagram\.com/([^"\'/]+)',
        'ok': r'ok\.ru/([^"\'/]+)',
        'telegram': r't\.me/([^"\'/]+)',
        'twitter': r'twitter\.com/([^"\'/]+)',
        'vk': r'vk\.com/([^"\'/]+)',
        'youtube': r'youtube\.\w+?(/channel/[^"\']+)',
    }
    for name, reg in regs.items():
        m = re.findall(reg, r.text, re.IGNORECASE)
        if m:
            found(name, m[0])


@interruptable
def check_contacts(_, r):
    """Check contacts"""
    regs = {
        'mail': r'[\w\-][\w\-\.]+@[\w\-][\w\-]+\.[\w]{1,5}',
        'phone': r'\+\d[-()\s\d]{5,}?(?=\s*[+<])',
        'tel': r'tel:(\+?[^\'"]+)',
        'mailto': r'mailto:(\+?[^\'"]+)',
    }
    contacts = defaultdict(set)
    for name, reg in regs.items():
        for m in re.findall(reg, r.text):
            if m.endswith(('png', 'svg')):
                continue
            contacts[name].add(m)
    for n, cc in contacts.items():
        for c in cc:
            found(n, c)


@interruptable
def check_cms(_, r):
    """Check CMS"""
    cmses = list(check_src(r.text, CMS_LIST))
    if cmses:
        found(', '.join(cmses))
    else:
        nfound('No CMS found in source')


@interruptable
def check_techs(_, r):
    """Check techs"""
    techs = list(check_src(r.text, TECH_LIST))
    if techs:
        found(', '.join(techs))
    else:
        nfound('No tech found')


@interruptable
def check_robots(url, _):
    """Check robots.txt"""
    urls = set()
    try:
        r = session.get('%s/robots.txt' % url, timeout=5, allow_redirects=False,
                        verify=False, stream=True, headers=headers)
        if r.status_code == 200:
            if 'Disallow' in r.text:
                for ln in r.text.splitlines():
                    if 'Disallow' in ln:
                        _, url = ln.split(None, 2)
                        urls.add(url.strip())
            if urls:
                found('Disallowed:', ', '.join(urls))
            else:
                nfound('No disallowed found')

            return
    except Exception as e:
        print(end='\r')
        err(repr(e))

    nfound('Get robots.txt failed')


@interruptable
def check_vulns(url, _):
    """Check vulns"""
    from functools import partial
    from concurrent.futures import ThreadPoolExecutor

    urlen = len(url) + 1

    for file, allow_html in FUZZ_FILES:

        process(tim(), 'Fuzz', file)

        with open(file) as f:
            progress = Progress(sum(1 for _ in f))
            f.seek(0)

            ff = ('%s%s' % (url, ln.rstrip()) for ln in f)
            check = partial(check_path, allow_html)

            with ThreadPoolExecutor() as ex:
                for r, rurl, cl in ex.map(check, ff):
                    path = rurl[urlen:]
                    if r:
                        print(end='\r')
                        found(tim(), '(%s)' % cl, path)
                    progress(path)


def main(url, nofuzz=False):
    print('='*42)
    print(BANNER.strip())
    print('Target:', url)
    print('='*42)

    tasks = [
        check_domains,
        check_headers,
        check_analytics,
        check_contacts,
        check_social,
        check_cms,
        check_techs,
        check_robots,
    ]

    if not nofuzz:
        tasks.append(check_vulns)

    url = iri_to_uri(url)

    try:
        initial_response = session.get(
            url, timeout=10, verify=False, headers=headers)
    except requests.ConnectionError as e:
        print(ERR, e, CEND)
        exit(e.errno)

    for task in tasks:
        print()
        process(task.__doc__)
        task(url, initial_response)


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    Fire(main)
