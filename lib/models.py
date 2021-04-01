from lib.files import CFG_DIR
from datetime import datetime

from pony.orm import Database, db_session
from pony.orm.core import Optional, PrimaryKey, Required, Set, commit, sql_debug
from pony.orm.ormtypes import Json, StrArray

from lib.files import LOCAL_DIR

DB_PATH = LOCAL_DIR / 'db.sqlite'

db = Database()


class Host(db.Entity):
    ip = Required(str, unique=True)
    created_at = Required(datetime, default=datetime.now())
    updated_at = Required(datetime, default=datetime.now())
    ports = Set('Port')
    comment = Optional(str)
    paths = Set('URLPath')

    def before_update(self):
        self.updated_at = datetime.now()


class Port(db.Entity):
    num = Required(int)
    created_at = Required(datetime, default=datetime.now())
    updated_at = Required(datetime, default=datetime.now())
    host = Required(Host)
    tags = Optional(str)
    banner = Optional(str)
    comment = Optional(str)
    data = Optional(Json)
    paths = Set('URLPath')


class Cred(db.Entity):
    user = Required(str)
    password = Optional(str)
    paths = Set('URLPath')


class URLPath(db.Entity):
    host = Required(Host)
    port = Required(Port)
    path = Required(str)
    cred = Optional(Cred)


@db_session
def add_path(host, port, path, cred=''):
    res = add_result(host, port)
    if not res:
        return
    h, p = res

    cr = None
    if cred:
        user, password = cred.split(':')
        cr = Cred(user=user, password=password)
    URLPath(host=h, port=p, path=path, cred=cr)


@db_session
def add_result(ip, port, comment='', tags=None, banner='', **kwargs):
    try:
        if tags is None:
            tags = []
        t = Host.get(ip=ip)
        if not t:
            t = Host(ip=ip)
        p = None
        for _p in t.ports:
            if _p.num == port:
                p = _p
        if not p:
            p = Port(num=port, host=t)
        tt = p.tags.split(',') if p.tags else []
        for tag in tags:
            if tag not in tt:
                tt.append(tag)
        p.tags = ','.join(tt)
        p.comment = comment[:255]
        p.banner = banner[:255]
        p.data = kwargs
        p.updated_at = datetime.now()
        t.updated_at = datetime.now()
        return (t, p)
    except Exception as e:
        print('error', repr(e))


@db.on_connect(provider='sqlite')
def sqlite_case_insensitive_like(_, connection):
    cursor = connection.cursor()
    cursor.execute('PRAGMA case_sensitive_like = OFF')


CFG = CFG_DIR / 'db.ini'

if CFG.exists():
    from configparser import ConfigParser
    cfg = ConfigParser()
    with CFG.open() as f:
        cfg.read_file(f)

    for section in cfg.sections():
        db_cfg = dict(cfg[section])
        if db_cfg.get('port'):
            db_cfg['port'] = int(db_cfg['port'])
        db.bind(**db_cfg)
else:
    db.bind(provider='sqlite', filename=str(DB_PATH), create_db=True)
db.generate_mapping(create_tables=True)
