#!/usr/bin/env python3
import os
import yaml
from PyInquirer import prompt

from lib.utils import str_to_filename

BANNER = r"""
 _     _  _        _  by fagci
| |__ | || |   ___| | __
| '_ \| || |_ / __| |/ /
| | | |__   _| (__|   <
|_| |_|  |_|  \___|_|\_\
"""

DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DIR = os.path.join(DIR, 'local')
SESSIONS_DIR = os.path.join(LOCAL_DIR, 'sessions')
CFG = os.path.join(LOCAL_DIR, 'session.yml')
MENU_CFG = os.path.join(DIR, 'cfg', 'menu.yml')


def write_config(file, data={}):
    with open(file, 'w') as f:
        if data:
            yaml.dump(data, f)
        return data


def read_config(file):
    if os.path.exists(file):
        with open(file) as f:
            return yaml.load(f, Loader=yaml.Loader) or {}
    else:
        return write_config(file)


def get_menu():
    with open(MENU_CFG) as f:
        return yaml.load(f, Loader=yaml.Loader)


def main():
    print()
    print('[!!! WARNING !!!]')
    print('This is prototype at this moment. Use tools directly.')
    print()

    cfg = read_config(CFG)

    session_name = ''

    if not os.path.exists(SESSIONS_DIR):
        os.mkdir(SESSIONS_DIR)

    menu = get_menu()
    session_files = sorted(list(os.walk(SESSIONS_DIR))[0][2])
    session_names = [f.rpartition('.')[0] for f in session_files]

    last_session = cfg.get('last_session')

    if last_session and last_session in session_names:
        if prompt(menu.get('restore_last_session')).get('restore'):
            session_name = last_session
        else:
            if session_names:
                session_name = prompt({
                    'type': 'list',
                    'name': 'session_name',
                    'message': 'Choose session',
                    'choices': session_names,
                }).get('session_name')
            else:
                session_name = prompt(
                    menu.get('new_session')).get('session_name')
                session_name = str_to_filename(session_name)

    session_name = session_name or 'default'
    session_file = os.path.join(SESSIONS_DIR, f'{session_name}.yml')

    session = read_config(session_file)

    cfg['last_session'] = session_name
    write_config(CFG, cfg)

    print(session_name)


if __name__ == "__main__":
    print('=' * 40)
    print(BANNER.lstrip('\n').rstrip())
    print('=' * 40)
    main()
