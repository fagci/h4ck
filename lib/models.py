from datetime import datetime

from pony.orm import Database, db_session
from pony.orm.core import Optional, PrimaryKey, Required, Set, commit, sql_debug
from pony.orm.ormtypes import Json, StrArray

from lib.files import LOCAL_DIR

DB_PATH = LOCAL_DIR / 'db.sqlite'

db = Database()


class Target(db.Entity):
    ip = Required(str, unique=True)
    created_at = Required(datetime, default=datetime.now())
    updated_at = Required(datetime, default=datetime.now())
    ports = Set('Port')
    comment = Optional(str)

    def before_update(self):
        self.updated_at = datetime.now()


class Port(db.Entity):
    num = Required(int)
    created_at = Required(datetime, default=datetime.now())
    updated_at = Required(datetime, default=datetime.now())
    target = Required(Target)
    tags = Optional(StrArray)
    banner = Optional(str)
    comment = Optional(str)
    data = Optional(Json)


@db_session
def add_result(ip, port, comment='', tags=None, banner='', **kwargs):
    try:
        if tags is None:
            tags = []
        t = Target.get(ip=ip)
        if not t:
            t = Target(ip=ip)
        p = None
        for _p in t.ports:
            if p.num == port:
                p = _p
        if not p:
            p = Port(num=port, target=t)
        for tag in tags:
            if tag not in p.tags:
                p.tags.append(tag)
        p.comment = comment
        p.banner = banner
        p.data = kwargs
        p.updated_at = datetime.now()
        t.updated_at = datetime.now()
    except Exception as e:
        print('error', repr(e))


@db.on_connect(provider='sqlite')
def sqlite_case_insensitive_like(_, connection):
    cursor = connection.cursor()
    cursor.execute('PRAGMA case_sensitive_like = OFF')


db.bind(provider='sqlite', filename=str(DB_PATH), create_db=True)
db.generate_mapping(create_tables=True)
