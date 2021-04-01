#!/usr/bin/env python3
from fire.core import Fire
from pony.orm.core import select
from pony.utils.utils import count

from lib.models import Port, Target, db_session, sql_debug


@db_session
def main(query='', port=None, tags=None, sdt=False, sp=True, sc=True, sb=False, sd=False, st=False):
    """Display stats or search in db"""
    if not any((query, port, tags)):
        print('Stats by port')
        select((p.num, p.tags, count(p)) for p in Port).show()
        return

    res = select(
        (p.created_at, t.ip, p.num, p.comment, p.banner, p.data, p.tags)
        for t in Target for p in t.ports
        if (
            query in p.comment
            or
            query in p.banner
            or
            query in t.ip
        )
        and
        (port == None or port == p.num)
        and
        (tags == None or tags in p.tags)
    )

    for d, ip, p, c, b, data, t in res:
        parts = []
        if sdt:
            parts.append(d.strftime('%m-%d %H:%M'))
        parts.append(ip)
        if sp:
            parts.append(p)
        if sc:
            parts.append(c)
        if sb:
            parts.append(b)
        if sd:
            parts.append(data)
        if st:
            parts.append(','.join(t))
        print(*parts)


if __name__ == "__main__":
    # sql_debug(True)
    Fire(main)
