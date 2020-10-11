#!/usr/bin/env python

""" 
Simple tcp sniffer
"""

import socket, struct

s = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0800))

def b2mac(bytes_addr):
    return ':'.join(map('{:02x}'.format, bytes_addr))

def main():
    while True:
        raw, _ = s.recvfrom(65535)

        eth_header = raw[:14]
        ip_header = raw[14:34]
        udp_header = raw[34:42]

        eth_struct = struct.unpack('!6s6sH', eth_header)

        proto_type = socket.ntohs(eth_struct[2])

        src_mac = b2mac(eth_struct[1])
        dst_mac = b2mac(eth_struct[0])

        if proto_type == 8: # IP
            ip_struct = struct.unpack('!BBHHHBBH4s4s', ip_header)
            src_ip = ip_struct[8]
            dst_ip = ip_struct[9]
            if ip_struct[6] == 0x11: # UDP
                pass # not implemented yet

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
