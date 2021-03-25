#!/usr/bin/env python3
from fire import Fire
from lib.utils import encode_ip


def main(ip, password):
    print(encode_ip(ip, password))


if __name__ == "__main__":
    Fire(main)
