#!/usr/bin/env python3

"""
Simple dns sniffer
"""

import socket, struct, binascii

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
            src_ip = socket.inet_ntoa(ip_struct[8])
            dst_ip = socket.inet_ntoa(ip_struct[9])

            if ip_struct[6] == 17: # UDP
                udp_struct = struct.unpack('!HHHH' , udp_header)
                src_port = udp_struct[0]
                dst_port = udp_struct[1]

                if dst_port == 53 or src_port == 53:
                    #dns_struct = struct.unpack("!2s2s2s2s2s2s", raw[42:54])
                    r = ''
                    domain_name_parts = raw[54:].split(b'\x00')[0]
                    for c in domain_name_parts:
                        if 48 <= c <= 57 or 65 <= c <= 90 or 97 <= c <= 122: r += chr(c)
                        else: r += '.'
                    print('{} > {}\n{}:{} > {}:{}'.format(src_mac, dst_mac, src_ip, src_port, dst_ip, dst_port))
                    print(r)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
