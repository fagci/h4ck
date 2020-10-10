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
        data, _ = s.recvfrom(65535)

        ethernet_header = data[:14]
        ip_header = data[14:34]
        tcp_header = data[34:54]

        dst_mac, src_mac, _ = struct.unpack('!6s6s2s', ethernet_header)
        ip_struct = struct.unpack('!BBHHHBBH4s4s', ip_header)
        if ip_struct[6] == 6:
            src_ip = ip_struct[8]
            dst_ip = ip_struct[9]
            src_port, dst_port, _ = struct.unpack('!HH16s', tcp_header)
            print('{} > {} {}:{} > {}:{}'.format(b2mac(src_mac), b2mac(dst_mac), socket.inet_ntoa(src_ip), src_port, socket.inet_ntoa(dst_ip), dst_port))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
