#!/usr/bin/env python3

from ftplib import FTP, FTP_TLS, error_perm, error_proto, error_reply, error_temp
from socket import timeout
from time import sleep

from fire import Fire

from lib.files import LOCAL_DIR
from lib.scan import check_port, generate_ips, process_each
from lib.utils import str_to_filename
from lib.models import add_result

FTP_FILES_PATH = LOCAL_DIR / 'ftp_files' / 'files'
FTP_LOGS_PATH = LOCAL_DIR / 'ftp_files' / 'logs'
FTP_LOG_PATH = LOCAL_DIR / 'ftp.txt'

INTERESTING_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
PATH_BLACKLIST = ('.', '..', 'bin')


def download_image(ftp, path):
    print('* DL', ftp.host, path)
    out_filename = '%s_%s' % (ftp.host, path.rpartition('/')[-1])
    out_path = str(FTP_FILES_PATH / str_to_filename(out_filename))
    r_cmd = ('RETR %s' % path)
    with open(out_path, 'wb') as of:
        ftp.retrbinary(r_cmd, of.write)


def traverse(ftp: FTP, depth=0, files=None):
    if files is None:
        files = []

    if depth > 10:
        print(ftp.host, 'too deep, leave')
        return

    paths = [p for p in ftp.nlst() if p not in PATH_BLACKLIST]

    for path in paths:
        files.append(path)
        with (FTP_LOGS_PATH / ('%s.txt' % ftp.host)).open('a') as f:
            f.write('%s\n' % path)
        if len(files) > 100:
            print(ftp.host, 'too many files, leave')
            return

        try:
            if path.lower().endswith(INTERESTING_EXTENSIONS):
                download_image(ftp, path)
                return path

            # skip files by extension delimiter
            if '.' in path:
                print('-', path)
                continue

            ftp.cwd(path)
            print(ftp.host, 'cd', path)
            found = traverse(ftp, depth+1, files)
            ftp.cwd('..')

            if found:
                return

        except error_perm:
            pass


def get_files(ftp: FTP):
    ip = ftp.host
    lst = [p for p in ftp.nlst() if p not in ('.', '..')]

    if not lst:
        print('-', ip, 'no files')
        return

    banner = ''
    try:
        banner = ftp.getwelcome()
    except:
        pass
    add_result(ip, 21, '%d file(s) in root' %
               len(lst), ['fortune'], banner)

    with FTP_LOG_PATH.open('a') as f:
        f.write('%s\n' % ip)

    print('Traverse', ip, 'start')
    res = traverse(ftp)
    print('Traverse', ip, 'end')

    return res


def process_ftp(ip, time):
    Connector: type[FTP] = FTP
    retries = 5

    while retries > 0:
        try:
            with Connector(ip, timeout=30) as ftp:
                ftp.login()
                print('~', ip, time, 'ms')
                try:
                    ftp.sendcmd('OPTS UTF8 ON')
                    ftp.encoding = 'utf-8'
                except:
                    pass
                return get_files(ftp)
        except (error_perm, error_proto) as e:
            if Connector is FTP:
                Connector = FTP_TLS
            else:
                break
        except (error_reply, error_temp) as e:
            try:
                code = int(str(e)[:3])
            except:
                break
            if code == 331 or code == 332:
                break  # anon login only
            if code == 421:
                break
            if code == 450:
                print('-', ip, e)
                break
            if code == 431:
                if Connector is FTP:
                    Connector = FTP_TLS
                    continue
                else:
                    break
            print(repr(e))
            break
        except OSError as e:
            pass
        except KeyboardInterrupt:
            print('Interrupted by user.')
            exit(130)
        except (EOFError, UnicodeDecodeError, timeout):
            break
        except Exception as e:
            print(repr(e))
            break
        retries -= 1
        sleep(1)


def check_host(ip, _):
    res = check_port(ip, 21)
    if res:
        process_ftp(ip, int(res[1]*1000))


def main(c=10_000_000, w=16):
    FTP_FILES_PATH.mkdir(exist_ok=True)
    FTP_LOGS_PATH.mkdir(exist_ok=True)
    print('Started.')
    process_each(check_host, generate_ips(c), w)
    print('Finished.')


if __name__ == "__main__":
    Fire(main)
