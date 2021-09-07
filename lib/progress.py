class Progress:
    prg = '|/-\\'
    prg_len = len(prg)

    def __init__(self, total=0):
        self.i = 0
        self.total = total
        self.val = ''
        self.update = self._progress if total else self._spin

    def _spin(self):
        self.i %= self.prg_len
        self.val = self.prg[self.i]

    def _progress(self):
        self.val = f'{self.i*100/self.total:3.2f}%'

    def __call__(self, desc=''):
        self.i += 1
        self.update()
        print(f'\r{self.val} {desc[-40:]}', end='\x1b[1K')
        if self.total != 0 and self.total == self.i:
            self.__del__()

    def __del__(self):
        print('\r', end='\x1b[1K\r', flush=True)
