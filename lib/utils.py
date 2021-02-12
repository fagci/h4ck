import sys


def interruptable(fn):
    def wrap(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except KeyboardInterrupt:
            print('\n[i] Interrupted by user. Exiting.')
            sys.exit(130)
    wrap.__doc__ = fn.__doc__
    return wrap


def tim():
    from datetime import datetime
    return datetime.now().strftime('%H:%M:%S')
