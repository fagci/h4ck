#!/usr/bin/env python
from urllib.request import urlopen
import sys

CRED = '\033[31m'
CGREEN = '\033[32m'
CYELLOW = '\033[33m'
CGREY = '\033[37m'
CDGREY = '\033[90m'
CEND = '\033[0m'

cmses = [
    'buttercms',
    'contao',
    'craft cms',
    'drupal',
    'expressionengine',
    'joomla',
    'magento',
    'neos cms',
    'octobercms',
    'opencart',
    'processwire',
    'pyrocms',
    'typo3',
    'wordpress',
    'yii',
]

techs = [
    'angular',
    'backbone',
    'bootstrap',
    'cordova',
    'elm',
    'ember',
    'firebase',
    'fontawesome',
    'ionic',
    'jquery',
    'laravel',
    'localstorage',
    'react',
    'select2',
    'serviceworker',
    'socketio',
    'sphinx',
    'svg',
    'tailwind',
    'vue',
    'webpack',
]


def get_headers(url):
    hdrs = ['Server', 'X-Powered-By']
    with urlopen(url) as u:
        items = u.info().items()
        return {hk: hv for hk, hv in items if hk in hdrs}


def check_path(url):
    try:
        with urlopen(url, timeout=1.2) as u:
            return u.getcode() == 200
    except KeyboardInterrupt:
        raise
    except:
        return False


def check_src(url):
    with urlopen(url) as u:
        html = u.read().decode().lower()
        for tech in cmses + techs:
            if tech in html:
                yield tech


with open('web_files.txt') as f:
    vuln_paths = [p.rstrip() for p in f]


def interruptable(fn):
    def wrap(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except KeyboardInterrupt:
            print('[i] Interrupted by user. Exiting.\n')
            exit(130)
    return wrap


@interruptable
def check_headers(url):
    print(f'{CDGREY}[*] Check headers...{CEND}\n')
    headers = get_headers(url)
    for hk, hv in headers.items():
        print(f'{CYELLOW}- {hk}: {hv}{CEND}\n')


@interruptable
def check_techs(url):
    print(f'{CDGREY}[*] Check techs...{CEND}\n')

    techs = check_src(url)
    if techs:
        for tech in techs:
            print(f'{CYELLOW}- {tech}{CEND}')
    else:
        print(f'{CGREY}[i] No tech found{CEND}')


@interruptable
def check_vulns(url):
    print(f'\n{CDGREY}[*] Check vulns...{CEND}\n')
    for vp in vuln_paths:
        if check_path(f'{url}/{vp}'):
            print(f'\n{CGREEN}[+] {vp}{CEND}')
        else:
            print(f'{CGREY}.{CEND}', end='', flush=True)


def main(url):
    print()
    print(f'Map CMS for {url}\n')

    check_headers(url)
    check_techs(url)
    check_vulns(url)


if __name__ == "__main__":
    main(sys.argv[1])
