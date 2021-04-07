#!/usr/bin/env python3
from fire.core import Fire
from pony.orm import db_session

from lib.models import Host, Port, sql_debug


@db_session
def main(query='', port='', tag='', sdt=False, sp=True, sc=True, sb=False, sd=False, st=False, d=False, limit=None):
    """Display stats or search in db"""
    from pony.orm.core import select

    if d:
        sql_debug(True)

    if not any((query, port, tag)):
        from pony.utils.utils import count

        print('Stats by port')
        select((p.num, p.tags, count(p)) for p in Port).show()

        print('Stats for rtsp')
        select((p.paths.cred.user, p.paths.cred.password, count()) for p in Port if p.num == 554).show()
        return

    res = select(
        (p.created_at, t.ip, p.num, p.comment, p.banner, p.data, p.tags)
        for t in Host for p in t.ports
        if (
            query in p.comment
            or
            query in p.banner
            or
            query in p.tags
            or
            query in str(p.num)
            or
            query in t.ip
        )
        and
        (tag in p.tags)
    ).limit(limit)

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
    Fire(main)
