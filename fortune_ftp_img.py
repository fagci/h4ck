#!/usr/bin/env python3

from ftplib import FTP, all_errors, error_perm
from socket import timeout

from fire import Fire

from lib.files import LOCAL_DIR
from lib.scan import generate_ips, check_port, process_each

FTP_FILES_PATH = LOCAL_DIR / 'ftp_files'
FTP_LOG_PATH = LOCAL_DIR / 'ftp.txt'

INTERESTING_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')


def download_image(ftp, filename):
    out_path = str(FTP_FILES_PATH / ('%s_%s' % (ftp.host, filename)))
    r_cmd = ("RETR %s" % filename).encode()
    with open(out_path, 'wb') as of:
        ftp.retrbinary(r_cmd, of.write)


def traverse(ftp: FTP, depth=0):
    if depth > 10:
        return
    for path in ftp.nlst():
        if path in ('.', '..'):
            continue
        print('>>', path)
        try:
            if path.endswith(INTERESTING_EXTENSIONS):
                print(path)
                download_image(ftp, path)
                return path

            ftp.cwd(path)
            found = traverse(ftp, depth+1)
            if found:
                return
            ftp.cwd('..')
        except error_perm:
            pass


def process_ftp(ip):
    try:
        with FTP(ip, timeout=10) as ftp:
            ftp.login()
            with FTP_LOG_PATH.open('a') as f:
                f.write('%s\n' % ip)
            traverse(ftp)
    except error_perm:
        return
    except EOFError:
        pass
    except UnicodeDecodeError:
        pass
    except timeout:
        pass
    except KeyboardInterrupt:
        print('Interrupted by user.')
        exit(130)
    except Exception as e:
        print(repr(e))
        pass


def check_host(ip, _):
    if check_port(ip, 21):
        process_ftp(ip)


def main(c=1000000, w=16):
    FTP_FILES_PATH.mkdir(exist_ok=True)
    process_each(check_host, generate_ips(c), w)


if __name__ == "__main__":
    Fire(main)
