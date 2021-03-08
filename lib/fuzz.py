from pathlib import Path
from lib.net import Connection, Response


class ListFile(list):
    def __init__(self, file_path):
        is_path = isinstance(file_path, Path)
        with file_path.open() if is_path else open(file_path) as f:
            self.extend(ln.rstrip() for ln in f)


class DictLoader:
    __slots__ = ('_dictionary', '_file_handler', '_items')

    def __init__(self, dictionary):
        self._dictionary = dictionary

    def __enter__(self):
        d = self._dictionary
        if isinstance(d, str):
            if '\n' in d:
                items = d.splitlines()
            else:
                self._file_handler = open(d)
                items = (ln.rstrip() for ln in self._file_handler)
        else:
            items = d

        self._items = iter(items)

        return self

    def __exit__(self, e_type, e_msg, e_trace):
        if self._file_handler:
            self._file_handler.close()
            self._file_handler = None
        self._items = None
        return e_type is None

    def __iter__(self):
        return self

    def __next__(self):
        return self._items.__next__()


class Brute:
    __slots__ = (
        '_connection',
        '_dictionary',
        '_path',
    )

    def __init__(self, connection: Connection, path: str, creds: list):
        self._connection = connection
        self._dictionary = creds
        self._path = path

    def run(self):
        for cred in self._dictionary:
            response = self._connection.auth(self._path, cred)

            if response.error:
                return

            if response.ok:
                return cred


class FuzzResult:
    __slots__ = ('path', 'ok', 'auth_needed')

    def __init__(self, path: str, response: Response):
        self.path = path
        self.ok = response.ok
        self.auth_needed = response.auth_needed


class Fuzz:
    __slots__ = (
        '_connection',
        '_dictionary',
    )

    def __init__(self, connection: Connection, dictionary: list):
        self._connection = connection
        self._dictionary = dictionary

    def check(self, path: str = '') -> Response:
        return self._connection.get(path)

    def __iter__(self):
        fake_path = '/fake_path'
        response = self.check(fake_path)

        if response.found:
            yield FuzzResult('/', response)
            return

        for path in self._dictionary:
            response = self.check(path)

            if response.error:
                return

            if response.found:
                yield FuzzResult(path, response)

            if response.auth_needed:
                yield FuzzResult(path, response)
