#!/usr/bin/env -S python -u
from functools import partial
from fire import Fire
from requests.sessions import Session
from lib.scan import check_port, generate_ips, process_each

__author__ = 'Mikhail Yudin aka fagci'

VULNS = [
    '.env',
    '.htpasswd',
    '.htaccess',
    'composer.json',
    'README.md',
    'README.txt',
    'log.txt',
    'data.txt',
    'accounts.txt',
    'pass.txt',
    'passes.txt',
    'passwords.txt',
    'pazz.txt',
    'pazzezs.txt',
    'pw.txt',
    'technico.txt',
    'usernames.txt',
    'users.txt',
    '.gitignore',
]


def check_url(session: Session, ip, port, path):
    s = 'https' if port == 443 else 'http'
    url = f'{s}://{ip}/{path}'
    try:
        r = session.get(url, allow_redirects=False,
                        timeout=3, verify=False, stream=True)
        return r.status_code == 200
    except:
        return False


def check_ip(ip, print_lock):
    for port in [80]:
        if check_port(ip, port):
            session = Session()
            cu = partial(check_url, session, ip, port)
            vulns_exists = map(cu, VULNS)
            if any(vulns_exists):
                with print_lock:
                    print('+', ip, port)


def check_ips(c: int = 200000, w: int = 1024):
    process_each(check_ip, generate_ips(c), w)


if __name__ == "__main__":
    Fire(check_ips)
