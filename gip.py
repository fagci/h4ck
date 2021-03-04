#!/usr/bin/env python3
from fire import Fire

from lib.utils import geoip_str_online


def main(ip: str):
    print(geoip_str_online(ip))


if __name__ == "__main__":
    Fire(main)
