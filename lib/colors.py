import colorama as cr

cr.init()

CF = cr.Fore
CRED = CF.RED
CGREEN = CF.GREEN
CYELLOW = CF.YELLOW
CLYELLOW = CF.LIGHTYELLOW_EX
CWHITE = CF.LIGHTWHITE_EX
CGREY = CF.WHITE
CDGREY = CF.LIGHTBLACK_EX
CEND = CF.RESET
CBLUE = CF.BLUE
CLBLUE = CF.LIGHTBLUE_EX
CLLBLUE = CF.CYAN

INFO = '%s[i]%s' % (CBLUE, CEND)
WARN = '%s[!]%s' % (CYELLOW, CEND)
ERR = '%s[E]%s' % (CRED, CEND)
QUEST = '%s[?]%s' % (CGREY, CEND)
FOUND = '%s[+]%s' % (CGREEN, CEND)
NFOUND = '%s[-]%s' % (CGREY, CEND)
PROCESS = '%s[*]%s' % (CWHITE, CEND)


def cprint(color, status, *args, **kwargs):
    print('%s%s %s' % (color, status, args[0]), *args[1:], CEND, **kwargs)


def info(*args, **kwargs):
    cprint(CBLUE, '[i]', *args, **kwargs)


def warn(*args, **kwargs):
    cprint(CYELLOW, '[!]', *args, **kwargs)


def err(*args, **kwargs):
    cprint(CRED, '[E]', *args, **kwargs)


def question(*args, **kwargs):
    cprint(CGREY, '[?]', *args, **kwargs)


def found(*args, **kwargs):
    cprint(CGREEN, '[+]', *args, **kwargs)


def nfound(*args, **kwargs):
    cprint(CGREY, '[-]', *args, **kwargs)


def process(*args, **kwargs):
    cprint(CWHITE, '[*]', *args, **kwargs)
