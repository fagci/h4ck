from urllib.request import urlopen
import sys

CRED = '\033[91m'
CGREEN = '\033[92m'
CYELLOW = '\033[93m'
CGREY = '\033[90m'
CEND = '\033[0m'


def get_server(url):
    with urlopen(url) as u:
        return u.info().get('Server')


def check_path(url):
    try:
        with urlopen(url, timeout=1.2) as u:
            return u.getcode() == 200
    except KeyboardInterrupt:
        raise
    except:
        pass


def check_src(url):
    cmses = [
        'yii',
        'wordpress',
        'magento',
        'drupal',
        'joomla',
        'opencart',
        'expressionengine',
        'pyrocms',
        'octobercms',
        'craft cms',
        'typo3',
        'contao',
        'neos cms',
        'processwire',
        'buttercms',

    ]
    techs = [
        'jquery',
        'select2',
        'angular',
        'vue',
        'bootstrap',
        'fontawesome',
        'socketio',
        'localstorage',
        'serviceworker',
        'react',
        'webpack',
        'svg',
        'ionic',
        'elm',
        'tailwind',
        'laravel',
        'sphinx',
        'ember',
        'backbone',
        'cordova',
        'firebase',
    ]
    with urlopen(url) as u:
        html = u.read().decode().lower()
        for tech in cmses + techs:
            if tech in html:
                yield tech


with open('web_files.txt') as f:
    vuln_paths = [p.rstrip() for p in f]


def main(url):
    print('[*] Check techs...\n')
    for tech in check_src(url):
        print(f'{CYELLOW}[i] {tech}{CEND}')

    print('\n[*] Check vulns...\n')
    for vp in vuln_paths:
        if check_path(f'{url}/{vp}'):
            print(f'{CGREEN}[+] {vp}{CEND}')
        else:
            print(f'{CGREY}[-] {vp}{CEND}')


if __name__ == "__main__":
    main(sys.argv[1])
