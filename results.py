#!/usr/bin/env python3
from fire.core import Fire
from pony.orm.core import select
from pony.utils.utils import count

from lib.models import Port, Target, db_session, sql_debug


@db_session
def main(query='', port=None):
    if not query:
        print('Stats by port')
        select((p.num, p.tags, count(p)) for p in Port).show()
        return

    res = select(
        (p.created_at, t.ip, p.num, p.comment)
        for t in Target for p in t.ports
        if (
            query in p.comment
            or
            query in p.banner
            or
            query in t.ip
        ) and (port == None or port == p.num)
    )

    for d, ip, p, c in res:
        print('{} {} {} {}'.format(
            d.strftime('%m-%d %H:%M'), ip, p, c))


if __name__ == "__main__":
    # sql_debug(True)
    Fire(main)
