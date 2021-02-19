import socket as so
import struct
from time import sleep
from time import time
import warnings

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

PORTS_WEB = [80, 443]
PORTS_MOST = [21, 22, 23, 25, *PORTS_WEB, 139, 445, 3306]

LINGER = struct.pack('ii', 1, 0)


def generate_ports(ports_list):
    from random import shuffle
    shuffle(ports_list)
    return list(ports_list)


def randip():
    """Get wide range random host IP"""
    from random import randint
    return so.inet_ntoa(struct.pack('>I', randint(1, 0xffffffff)))


def generate_ips(count: int, bypass_local=True):
    """Get wide range random host IPs"""
    for _ in range(count):
        if bypass_local:
            while True:
                ip = randip()
                if ip.startswith((
                    '10.',
                    '169.254.',
                    '172.16.',
                    '172.17.',
                    '172.18.',
                    '172.19.',
                    '172.20.',
                    '172.21.',
                    '172.22.',
                    '172.23.',
                    '172.24.',
                    '172.25.',
                    '172.26.',
                    '172.27.',
                    '172.28.',
                    '172.29.',
                    '172.30.',
                    '172.31.',
                    '192.168.',
                    '127.'
                )):
                    continue
                yield ip
                break
        else:
            yield randip()


def check_port(ip, port, timeout=1, double_check=False, iface: str = None):
    target = (ip, port)
    while True:
        try:
            with so.socket() as s:
                # send only RST on close
                s.setsockopt(so.SOL_SOCKET, so.SO_LINGER, LINGER)
                s.setsockopt(so.IPPROTO_TCP, so.TCP_NODELAY, 1)
                if iface:
                    s.setsockopt(
                        so.SOL_SOCKET, so.SO_BINDTODEVICE, iface.encode())
                s.settimeout(timeout)
                t = time()
                res = s.connect_ex(target) == 0

                if double_check and not res:
                    double_check = False
                    continue
                elapsed = time() - t
                return (res, elapsed) if res else None
        except KeyboardInterrupt:
            raise
        except OSError as e:
            if e.errno == 24:
                sleep(0.15)
                continue
            break


def check_url(ip, port, path):
    from requests import get
    s = 'https' if port == 443 else 'http'
    url = f'{s}://{ip}/{path}'
    try:
        r = get(url, allow_redirects=False,
                timeout=3, verify=False, stream=True)
        return r.status_code == 200
    except:
        return False


def get_banner(ip, port, timeout=3, send=None):
    while True:
        try:
            with so.socket() as s:
                # send only RST on close
                s.setsockopt(so.SOL_SOCKET, so.SO_LINGER, LINGER)
                s.settimeout(timeout)
                if s.connect_ex((ip, port)) == 0:
                    if send:
                        s.send(send.encode())
                    elif port not in (21,):
                        s.send('Hello\r\n'.encode())
                    banner = s.recv(1024).decode()
                    for ln in banner.splitlines():
                        if any(x in ln.lower() for x in ('ssh', 'ftp', 'samba')) or (ln.strip()):
                            return ln.strip()
        except OSError as e:
            if e.errno == 24:
                sleep(0.15)
                continue
            break


def process(fn, it, workers=16, *args):
    from threading import Lock, Thread
    from time import sleep

    threads = []
    gen_lock = Lock()
    print_lock = Lock()

    for _ in range(workers):
        t = Thread(target=fn, daemon=True, args=(
            it, gen_lock, print_lock, *args))
        threads.append(t)

    for t in threads:
        t.start()

    while any(map(lambda t: t.is_alive(), threads)):
        sleep(0.25)
