#!/usr/bin/env python3
from scapy.all import sniff
from scapy.layers.inet import TCP


def pkt_recv(pkt):
    if pkt.haslayer(TCP):
        r: TCP = pkt[TCP]
        if r.payload and 'DESCRIBE' not in r.payload:
            print(r.payload)


if __name__ == '__main__':
    sniff(prn=pkt_recv, store=0, filter='port 554', iface='tun0')
