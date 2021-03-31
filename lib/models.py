from pony.orm import Database, db_session
from pony.orm.core import Entity, Optional, PrimaryKey, Required, Set, commit, sql_debug
from datetime import datetime

from pony.orm.ormtypes import StrArray
from lib.files import LOCAL_DIR

DB_PATH = LOCAL_DIR / 'db.sqlite'

db = Database()


class Target(db.Entity):
    ip = PrimaryKey(str)
    created_at = Required(datetime, default=datetime.now())
    updated_at = Required(datetime, default=datetime.now())
    ports = Set('Port')
    comment = Optional(str)

    def before_update(self):
        self.updated_at = datetime.now()


class Port(db.Entity):
    num = Required(int)
    comment = Optional(str)
    targets = Set(Target)
    tags = Optional(StrArray)


@db_session
def add_result(ip, port, comment='', tags=None):
    try:
        if tags is None:
            tags = []
        t = Target.get(ip=ip)
        if not t:
            t = Target(ip=ip)
        if port not in t.ports.num:
            t.ports.add(Port(num=port, comment=comment))
        for p in t.ports:
            if p.num == port:
                for tag in tags:
                    p.tags.append(tag)
        t.updated_at = datetime.now()
    except Exception as e:
        print('error', repr(e))


db.bind(provider='sqlite', filename=str(DB_PATH), create_db=True)
db.generate_mapping(create_tables=True)