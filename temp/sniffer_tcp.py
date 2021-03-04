#!/usr/bin/env python3
"""Simple tcp sniffer"""

import socket
import struct

s = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0800))


def b2mac(bytes_addr):
    return ':'.join(map('{:02x}'.format, bytes_addr))


def main():
    while True:
        raw, _ = s.recvfrom(65535)

        eth_header = raw[:14]
        ip_header = raw[14:34]
        tcp_header = raw[34:54]
        data = raw[54:]

        eth_struct = struct.unpack('!6s6sH', eth_header)

        proto_type = socket.ntohs(eth_struct[2])

        src_mac = b2mac(eth_struct[1])
        dst_mac = b2mac(eth_struct[0])

        if proto_type == 8:  # IP
            ip_struct = struct.unpack('!BBHHHBBH4s4s', ip_header)
            src_ip = ip_struct[8]
            dst_ip = ip_struct[9]
            if ip_struct[6] == 6:  # TCP
                src_port, dst_port, _ = struct.unpack('!HH16s', tcp_header)
                print('\n{} > {}\n{}:{} > {}:{}'.format(src_mac, dst_mac, socket.inet_ntoa(
                    src_ip), src_port, socket.inet_ntoa(dst_ip), dst_port))
                if b'HTTP' in data:
                    ln = data.split(b'\r\n')
                    for l in ln:
                        try:
                            print(str(l))
                        except Exception as e:
                            print(e)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
