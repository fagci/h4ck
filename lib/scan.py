import socket as so
import warnings

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

PORTS_WEB = [80, 443]
PORTS_MOST = [21, 22, 23, 25, *PORTS_WEB, 139, 445, 3306]


def generate_ports(ports_list):
    from random import shuffle
    shuffle(ports_list)
    return list(ports_list)


def generate_ips(count: int):
    from random import randrange
    while count > 0:
        a = randrange(1, 256)
        b = randrange(0, 256)
        c = randrange(0, 256)
        d = randrange(1, 255)
        ip = f'{a}.{b}.{c}.{d}'
        if ip.startswith(('10.', '172.', '192.168.', '127.')):
            continue
        count -= 1
        yield ip


def check_port(ip, port, timeout=0.2):
    while True:
        try:
            with so.socket() as s:
                s.settimeout(timeout)
                return s.connect_ex((ip, port)) == 0
        except so.error:
            continue


def check_url(ip, port, path):
    from requests import get
    s = 'https' if port == 443 else 'http'
    url = f'{s}://{ip}/{path}'
    try:
        r = get(url, allow_redirects=False, timeout=1, verify=False)
        return r.status_code == 200
    except:
        return False


def get_banner(ip, port, timeout=0.5):
    try:
        with so.socket() as s:
            s.settimeout(timeout)
            if s.connect_ex((ip, port)) == 0:
                if port not in (21,):
                    s.send('Hello\r\n'.encode())
                banner = s.recv(1024).decode()
                for ln in banner.splitlines():
                    if any(x in ln.lower() for x in ('ssh', 'ftp', 'samba')) or (ln.strip()):
                        return ln.strip()
    except:
        pass


def process(fn, it, workers=16):
    from threading import Lock, Thread
    from time import sleep
    threads = []
    gen_lock = Lock()
    print_lock = Lock()

    for _ in range(workers):
        t = Thread(target=fn, daemon=True, args=(it, gen_lock, print_lock,))
        threads.append(t)

    for t in threads:
        t.start()

    while any(map(lambda t: t.is_alive(), threads)):
        sleep(0.25)
