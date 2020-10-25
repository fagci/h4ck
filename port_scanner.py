#!/usr/bin/env python
import socket
from queue import Queue
from threading import Thread

port_from = 0
port_to = 10000
threads_count = 20

queue = Queue()
socket.setdefaulttimeout(0.25)
target_ip = socket.gethostbyname('127.0.0.1')

def port_check(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if s.connect_ex((target_ip, port)) == 0:
        print(f'{port} open')

    s.close()


def scan_thread():
    while True:
        port = queue.get()
        port_check(port)
        queue.task_done()


def main():
    for _ in range(threads_count):
        Thread(target=scan_thread,daemon=True).start()

    for port in range(port_from, port_to):
        queue.put(port)

    queue.join()


if __name__ == "__main__":
    main()
