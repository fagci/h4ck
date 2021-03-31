#!/usr/bin/env python3
from fire import Fire
from pony.orm.core import select
from pony.utils.utils import count
from lib.models import Port, Target, db_session


@db_session
def main(comment=''):
    if comment:
        print('Search by comment')
        select((t.ip, t.ports.num, t.ports.comment)
               for t in Target for p in t.ports if str(comment) in p.comment).show()
        return

    print('Stats by port')
    select((p.num, p.tags, count(p)) for p in Port).show()


if __name__ == "__main__":
    Fire(main)
