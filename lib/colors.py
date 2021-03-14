import colorama as cr

cr.init()

CF = cr.Fore
CRED = CF.RED
CGREEN = CF.GREEN
CYELLOW = CF.YELLOW
CGREY = CF.WHITE
CDGREY = CF.LIGHTBLACK_EX
CEND = CF.RESET
CBLUE = CF.BLUE
CLBLUE = CF.LIGHTBLUE_EX

INFO = '%s[i]%s' % (CBLUE, CEND)
WARN = '%s[!]%s' % (CYELLOW, CEND)
ERR = '%s[E]%s' % (CRED, CEND)
QUEST = '%s[?]%s' % (CGREY, CEND)
FOUND = '%s[+]%s' % (CGREEN, CEND)
NFOUND = '%s[-]%s' % (CGREY, CEND)
PROCESS = '%s[*]%s' % (CGREY, CEND)
