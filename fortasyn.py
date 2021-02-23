#!/usr/bin/env python
import asyncio
from time import time

from lib.scan import generate_ips


async def check(host, port, timeout=4):
    c = asyncio.open_connection(host, port)
    while True:
        try:
            t = time()
            await asyncio.wait_for(c, timeout)
            c.close()
            res = host, port, int((time()-t)*1000)
            return res
        except OSError as e:
            if e.errno == 24:
                await asyncio.sleep(0.5)
                continue
        except Exception as e:
            return None


async def scan(port=554):
    aw = (check(h, port) for h in generate_ips(1000))
    r = await asyncio.gather(*aw, return_exceptions=True)
    res = []
    for h, p, t in filter(lambda res: res, r):
        print(f'{t:>4} ms {h}:{p}')
        res.append(h)
    return res


def main():
    ips = []
    while len(ips) < 1024:
        ips += asyncio.run(scan())


if __name__ == "__main__":
    main()
