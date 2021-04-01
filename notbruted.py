#!/usr/bin/env python3
from fire.core import Fire
from pony.orm.core import select
from pony.utils.utils import count

from lib.models import Port, Host, Cred, URLPath, db_session, sql_debug


@db_session
def main():
    select(
        up.host.ip
        for c in Cred if c.user == '?'
        for up in c.paths
    ).show()


if __name__ == "__main__":
    # sql_debug(True)
    Fire(main)
