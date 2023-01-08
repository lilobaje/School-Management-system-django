import os
import re
from mysqlx import db
from jinja2 import Template
from mysqlx.model import SqlModel
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

_REGEX = '{%|{{|}}|%}'
_SQL_CONTAINER = dict()


def init_db(user, password, database, host='127.0.0.1', port=3306, use_unicode=True, pool_size=5, mapper_path='mapper', **kw):
    _load_sql(mapper_path)
    db.init_db(user, password, database, host, port, use_unicode, pool_size, **kw)


def insert(table, **kw):
    return db.insert(table, **kw)


def execute(sql_id, *args, **kwargs):
    sql = get_sql(sql_id, **kwargs)
    return db.execute(sql, *args, **kwargs)


def batch_execute(sql_id, args: list):
    sql = get_sql(sql_id)
    return db.batch_execute(sql, args)


def get(sql_id, *args, **kwargs):
    sql = get_sql(sql_id, **kwargs)
    return db.get(sql, *args, **kwargs)


def select_one(sql_id, *args, **kwargs):
    sql = get_sql(sql_id, **kwargs)
    return db.select_one(sql, *args, **kwargs)


def select(sql_id, *args, **kwargs):
    sql = get_sql(sql_id, **kwargs)
    return db.select(sql, *args, **kwargs)


def get_connection():
    return db.get_connection()


def _get_path(path):
    if path.startswith("../"):
        rpath = ''.join(re.findall("../", path))
        os.chdir(rpath)
        path = path[len(rpath):]
    elif path.startswith("./"):
        path = path[2:]
    return os.path.join(os.getcwd(), path)


def _load_sql(path):
    if not os.path.isabs(path):
        path = _get_path(path)

    for f in os.listdir(path):
        file = os.path.join(path, f)
        if os.path.isfile(file) and f.endswith(".xml"):
            _read_mapper(file)
        elif os.path.isdir(file):
            _load_sql(file)


def _read_mapper(file):
    global _SQL_CONTAINER
    tree = ET.parse(file)
    root = tree.getroot()
    namespace = root.attrib.get('namespace', '')
    for child in root:
        sql_id = namespace + "." + child.attrib.get('id')
        include = child.attrib.get('include')
        sql = child.text
        if include or re.search(_REGEX, sql):
            _SQL_CONTAINER[sql_id] = SqlModel(sql=Template(sql), dynamic=True, include=include)
        else:
            _SQL_CONTAINER[sql_id] = SqlModel(sql=sql)


def get_sql(sql_id, **kwargs):
    sql_model = _get_sql_model(sql_id)
    includes = sql_model.include
    if includes:
        for include in includes.split(","):
            include_sql_id = sql_id[:sql_id.index(".")+1] + include
            kwargs[include] = get_sql(include_sql_id, **kwargs)
    return sql_model.sql.render(**kwargs) if sql_model.dynamic else sql_model.sql


def _get_sql_model(sql_id):
    global _SQL_CONTAINER
    return _SQL_CONTAINER[sql_id]

