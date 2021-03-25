#!/usr/bin/env python3
from fire import Fire


def main(password, text):
    b = str(text).encode()
    passlen = len(password)
    b = map(lambda v: ord(password[v[0] % passlen]) ^ v[1], enumerate(b))
    print(bytes(b).decode())


if __name__ == "__main__":
    Fire(main)
