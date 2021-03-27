#!/usr/bin/env python3

from ftplib import FTP, FTP_TLS, error_perm, error_proto, error_temp
from socket import timeout
from time import sleep

from fire import Fire

from lib.files import LOCAL_DIR
from lib.scan import check_port, generate_ips, process_each
from lib.utils import str_to_filename

FTP_FILES_PATH = LOCAL_DIR / 'ftp_files'
FTP_LOG_PATH = LOCAL_DIR / 'ftp.txt'

INTERESTING_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')


def download_image(ftp, filename):
    out_filename = '%s_%s' % (ftp.host, filename.rpartition('/')[-1])
    out_path = str(FTP_FILES_PATH / str_to_filename(out_filename))
    r_cmd = ('RETR %s' % filename)
    with open(out_path, 'wb') as of:
        ftp.retrbinary(r_cmd, of.write)


def traverse(ftp: FTP, depth=0, files=[]):
    if depth > 10:
        return
    for path in ftp.nlst():
        if path in ('.', '..'):
            continue
        print('+', path)
        files.append(path)
        if len(files) > 100:
            return  # we don't want wait more
        try:
            if path.endswith(INTERESTING_EXTENSIONS):
                download_image(ftp, path)
                return path

            ftp.cwd(path)
            found = traverse(ftp, depth+1, files)
            if found:
                return
            ftp.cwd('..')
        except error_perm:
            pass


def process_ftp(ip):
    Connector = FTP_TLS
    retries = 5
    while retries > 0:
        try:
            with Connector(ip, timeout=10) as ftp:
                ftp.login()
                lst = ftp.nlst()
                if not lst:
                    return
                print(ip, 'lst:', *lst, sep='\n')
                with FTP_LOG_PATH.open('a') as f:
                    f.write('%s\n' % ip)
                return traverse(ftp)
        except error_perm as e:
            print(repr(e))
            if Connector is FTP_TLS:
                Connector = FTP
                print('switch to simple ftp')
            else:
                return
            return
        except error_temp as e:
            print(repr(e))
            if str(e).startswith('431') and Connector is FTP_TLS:
                Connector = FTP
                print('switch to simple ftp')
            else:
                return
        except error_proto:
            if Connector is FTP_TLS:
                Connector = FTP
                print('switch to simple ftp')
            else:
                return
        except EOFError:
            return
        except UnicodeDecodeError as e:
            print(repr(e))
            return
        except timeout:
            sleep(1)
            retries = 2  # one more try
        except OSError:
            sleep(2)
        except KeyboardInterrupt:
            print('Interrupted by user.')
            exit(130)
        except Exception as e:
            print(repr(e))
            return
        retries -= 1


def check_host(ip, _):
    if check_port(ip, 21):
        process_ftp(ip)


def main(c=10_000_000, w=16):
    FTP_FILES_PATH.mkdir(exist_ok=True)
    process_each(check_host, generate_ips(c), w)


if __name__ == "__main__":
    Fire(main)