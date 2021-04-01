#!/usr/bin/env python3
from fire import Fire
from pony.orm.core import select
from pony.utils.utils import count
from lib.models import Port, Target, db_session, sql_debug


@db_session
def main(comment='', banner='', ip='', limit=20):
    if not any((comment, banner, ip)):
        print('Stats by port')
        select((p.num, p.tags, count(p)) for p in Port).show()
        return

    select((t.ip, t.ports.num, t.ports.comment)
           for t in Target for p in t.ports if (
               str(comment) in p.comment
               and
               str(ip) in t.ip
               and
               str(banner) in p.banner
    )).limit(limit).show()


if __name__ == "__main__":
    # sql_debug(True)
    Fire(main)
