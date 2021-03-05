#!/usr/bin/env python3
from queue import Queue
from threading import Thread
from time import sleep

from lib.scan import generate_ips


class Work(Thread):
    q_in: Queue
    q_out: Queue
    workers: list[Thread]

    def __init__(self, workers_count=16, qo_size=16):
        super().__init__()
        self.q_out = Queue(qo_size)
        self._workers_count = workers_count

        self.workers = []
        self.setDaemon(True)

    def work(self):
        while True:
            if self.q_out.not_full:
                self.q_out.put(self.q_in.get())

    def run(self):
        for _ in range(self._workers_count):
            w = Thread(target=self.work, daemon=True)
            w.start()

    def __or__(self, b: 'Work'):
        b.q_in = self.q_out
        return b

    def __ror__(self, b: 'Work'):
        b.q_in = self.q_out
        return b

    def __iter__(self):
        while any(map(lambda x: x.is_alive(), self.workers)):
            sleep(0.25)
            yield self.q_out.get(timeout=10)


class HostGen(Work):
    def run(self):
        self.ips = generate_ips(100)
        super().run()

    def work(self):
        while True:
            if self.q_out.not_full:
                self.q_out.put(next(self.ips))


class Fuzzer(Work):
    pass


def main():
    hosts = HostGen()
    fuzzer = Fuzzer()

    print('Connecting')

    results = hosts | fuzzer

    print('Connected')

    fuzzer.start()
    hosts.start()

    for result in results:
        print(result)

    results.join()


if __name__ == "__main__":
    main()
