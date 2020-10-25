#!/usr/bin/env python
from requests import get

base_url = 'https://mikhail-yudin.ru'

def main():
    response = get(base_url)
    server = response.headers.get('Server')
    print(f'Server: {server}')

if __name__ == "__main__":
    main()
