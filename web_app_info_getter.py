#!/usr/bin/env python
from requests import get
from urllib.parse import urlparse
import ssl, socket

base_url = 'https://mikhail-yudin.ru'

def get_cert_info(url):
    p_url = urlparse(url)
    ctx = ssl.create_default_context()
    with ctx.wrap_socket(socket.socket(), server_hostname=p_url.netloc) as s:
        s.connect((p_url.netloc, 443))
        cert = s.getpeercert()

    subject = dict(x[0] for x in cert['subject'])
    issued_to = subject['commonName']
    issuer = dict(x[0] for x in cert['issuer'])
    issued_by = issuer['commonName']
    print(cert)

def main():
    response = get(base_url)
    h = response.headers
    server = h.get('Server')
    xct = 'nosniff' not in h.get('X-Content-Type-Options','')
    mitm = not h.get('Strict-Transport-Security', False)
    csp = not h.get('Content-Security-Policy', False)
    print(f'Server: {server}. Vulns: xct {xct}, mitm {mitm}, csp {csp}')
    get_cert_info(base_url)

if __name__ == "__main__":
    main()
