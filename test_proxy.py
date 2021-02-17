#!/usr/bin/env python
import socks as so
import proxyscrape
# Create a collector for http resources
collector = proxyscrape.create_collector('my-collector', 'socks4')
proxy: proxyscrape.Proxy = collector.get_proxy(
    {'country': 'united states'})  # Retrieve a united states proxy


with so.socksocket() as s:
    s.set_proxy(so.SOCKS4, proxy.host, int(proxy.port))
    s.connect(('checkip.dyndns.org', 80))
    s.send('GET / HTTP/1.1\r\n\r\n'.encode())
    print(s.recv(1024).decode())
