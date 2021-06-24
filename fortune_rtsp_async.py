#!/usr/bin/env python3

import asyncio

from lib.scan import generate_ips
from lib.net import RTSPConnection

from fire import Fire

async def worker(q_in, q_out, port, timeout=1.5):
    while True:
        ip = await q_in.get()
        with RTSPConnection(ip, port, timeout=timeout) as c:
            r = c.query()

            if r.found and 'PLAY' in r.headers.get('public', ''):
                print(ip)
                q_out.put_nowait(ip)

        q_in.task_done()

async def filler(q_in, tasks_q_filled, limit):
    for ip in generate_ips(limit):
        await q_in.put(ip)
    tasks_q_filled.set()

async def main(port=554, t=1.5, w=256, l=20000):
    tasks_q = asyncio.Queue(w)
    out_q = asyncio.Queue()
    tasks_q_filled = asyncio.Event()

    tasks = [asyncio.create_task(filler(tasks_q, tasks_q_filled, l))]

    for _ in range(w):
        f = worker(tasks_q, out_q, port, t)
        task = asyncio.create_task(f)
        tasks.append(task)

    await tasks_q_filled.wait()
    await tasks_q.join()

    for task in tasks:
        task.cancel()

    # while out_q.qsize():
    #     print(out_q.get_nowait(), flush=True)

if __name__ == '__main__':
    Fire(main)
