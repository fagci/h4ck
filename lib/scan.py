import socket as so
import struct
from time import sleep
from time import time
from typing import Callable
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
    start = time()
    target = (ip, port)

    while time() - start < 2:
        try:
            with so.socket() as s:
                # send only RST on close
                s.setsockopt(so.SOL_SOCKET, so.SO_LINGER, LINGER)
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
        except so.timeout:
            break
        except OSError:
            sleep(0.5)
        except:
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
                        s.sendall(send.encode())
                    elif port not in (21,):
                        s.sendall('OPTIONS * HTTP/1.1\r\n\r\n'.encode())
                    banner = s.recv(1024).decode()
                    for ln in banner.splitlines():
                        if any(x in ln.lower() for x in ('ssh', 'ftp', 'samba')) or (ln.strip()):
                            return ln.strip()
        except OSError as e:
            if e.errno == 24:
                sleep(0.15)
                continue
            break


def process_each(fn, it, workers=16, *args):
    running = True

    def fn2(gen, gl, pl, running, *args):
        while running:
            try:
                with gl:
                    item = next(gen)
            except StopIteration:
                break
            try:
                fn(item, pl, *args)
            except:
                running = False
                break

    process(fn2, iter(it), workers, running, *args)


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
        sleep(0.5)


def process_threaded(fn: Callable, items: list, callback: Callable = lambda _: True, progress: bool = True, workers: int = None):
    from tqdm import tqdm
    from concurrent.futures import ThreadPoolExecutor, as_completed

    total = len(items)
    results = []

    with ThreadPoolExecutor(workers) as ex:
        with tqdm(total=total, disable=not progress) as prg:
            futures = []

            for item in items:
                future = ex.submit(fn, item)
                future.add_done_callback(lambda _: prg.update())
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                cb_result = callback(result)

                if cb_result:
                    results.append(result)

    return results


async def process_threaded_async(fn: Callable, items, workers: int = None):
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    results = []

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(workers) as ex:
        futures = []

        for item in items:
            future = loop.run_in_executor(ex, fn, item)
            futures.append(future)

        for future in asyncio.as_completed(futures):
            result = await future

            if result:
                results.append(result)

    return results


def get_domains_from_cert(hostname, port: int = 443, timeout: float = 10):
    import ssl
    import socket

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.VerifyMode.CERT_NONE

    with context.wrap_socket(socket.socket(), server_hostname=hostname) as c:
        c.settimeout(timeout)
        c.connect((hostname, port))

        ssl_info = c.getpeercert()

        return [v for _, v in ssl_info.get('subjectAltName', [])]
