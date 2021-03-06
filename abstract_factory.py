#!/usr/bin/env python3
from queue import Queue
from threading import Thread
from time import sleep

from lib.scan import generate_ips


class Node:
    source = []
    sink = None

    @staticmethod
    def connect(source, sink):
        sink.sink = source.source
        print(type(source), '>', type(sink))
        return sink

    def init(self):
        """Overload to realise logic"""
        self.source = self.sink

    def __or__(self, sink: 'Node'):
        return self.connect(self, sink)

    def __ror__(self, source: 'Node'):
        return self.connect(source, self)

    def __iter__(self):
        self.init()
        yield from self.source


class HostGen(Node):
    def __init__(self):
        self.source = generate_ips(100)


class Fuzzer(Node):
    pass


def main():
    hosts = HostGen()
    d1 = Node()
    d2 = Node()
    fuzzer = Fuzzer()

    results = hosts | d1 | d2 | fuzzer

    for result in results:
        print(result)


if __name__ == "__main__":
    main()
