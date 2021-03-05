from lib.net import Connection, Response


class DictLoader:
    __slots__ = (
        '_dictionary',
        '_items',
        '_file_handler',
    )

    def __init__(self, dictionary):
        self._dictionary = dictionary

    def __enter__(self):
        if isinstance(self._dictionary, str):
            if '\n' in self._dictionary:
                self._items = iter(self._dictionary.splitlines())
            else:
                self._file_handler = open(self._dictionary)
                self._items = (ln.rstrip() for ln in self._file_handler)
        else:
            self._items = iter(self._dictionary)

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


class Bruter(DictLoader):
    def __init__(self, connection: Connection, dictionary: str, path: str):
        self._connection = connection
        self._path = path
        super().__init__(dictionary)

    def __iter__(self):
        response = Response()
        for cred in self._items:
            response = self._connection.auth(self._path, cred)
            if response.error:
                return
            if response.ok:
                yield cred, True
            else:
                yield cred, False


class Fuzzer(DictLoader):
    __slots__ = (
        '_connection',
    )

    def __init__(self, connection: Connection, dictionary: str):
        self._connection = connection
        super().__init__(dictionary)

    def check(self, path: str = '') -> Response:
        return self._connection.get(path)

    def __iter__(self):
        for path in self._items:
            response = self.check(path)

            if response.error:
                return

            if response.found:
                yield path, False
            if response.auth_needed:
                yield path, True
