#!/usr/bin/env python3

from ftplib import FTP, all_errors, error_perm

from fire import Fire

from lib.files import LOCAL_DIR
from lib.utils import dt
from lib.scan import generate_ips, check_port, process_each

FTP_FILES_PATH = LOCAL_DIR / 'ftp_files'


def traverse(ftp, depth=0):
    if depth > 10:
        return
    for entry in (path for path in ftp.nlst() if path not in ('.', '..')):
        try:
            if entry.endswith(('.jpg', '.jpeg', '.png')):
                print(entry)
                filename = str(FTP_FILES_PATH / ('%s_%s' % (dt, entry)))
                r_cmd = ("RETR %s" % entry).encode()
                with open(filename, 'wb') as of:
                    ftp.retrbinary(r_cmd, of.write)
            ftp.cwd(entry)
            traverse(ftp, depth+1)
            ftp.cwd('..')
        except error_perm as e:
            # print(repr(e), entry)
            pass


def download_image(ip):
    try:
        with FTP(ip) as ftp:
            ftp.login()
            traverse(ftp)
    except error_perm:
        return
    except Exception as e:
        print(repr(e))
        pass


def check_host(ip, _):
    if check_port(ip, 21):
        download_image(ip)


def main(c=1000000, w=16):
    FTP_FILES_PATH.mkdir(exist_ok=True)
    process_each(check_host, generate_ips(c), w)


if __name__ == "__main__":
    Fire(main)
