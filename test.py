from lib.net import RTSPConnection
import timeit

parts = {
    'realm': ',',
    'nonce': ',',
}


def main():
    return RTSPConnection.get_digest_auth_header(parts, RTSPConnection.M_DESCRIBE, '/', 'user', 'user')


if __name__ == "__main__":
    print(timeit.timeit(main))
