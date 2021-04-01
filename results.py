#!/usr/bin/env python3
import sys

from pony.orm.core import select
from pony.utils.utils import count

from lib.models import Port, Target, db_session, sql_debug


@db_session
def main(query=''):
    query = str(query).lower()

    if not query:
        print('Stats by port')
        select((p.num, p.tags, count(p)) for p in Port).show()
        return

    select(
        (t.ip, p.num, p.comment)
        for t in Target
        for p in t.ports
        if
        query in p.comment.lower()
        or
        query in p.banner.lower()
        or
        query in t.ip
    ).show()


if __name__ == "__main__":
    # sql_debug(True)
    main(' '.join(sys.argv[1:]))
