import re, time, functools, logging
from mysqlx.model import DBCtx, ConnectionCtx, Dict, MultiColumnsError, TransactionCtx

# thread-local context:
_DB_CTX = None
_REGEX = r':[\w|\d]*'


def init_db(user, password, database, host='127.0.0.1', port=3306, use_unicode=True, pool_size=5, **kwargs):
    from mysql.connector import connect
    global _DB_CTX
    if pool_size is not None and 'pool_name' not in kwargs:
        kwargs['pool_name'] = database + "_pool"

    kwargs['user'] = user
    kwargs['password'] = password
    kwargs['database'] = database
    kwargs['host'] = host
    kwargs['port'] = port
    kwargs['use_unicode'] = use_unicode
    _DB_CTX = DBCtx(lambda: connect(**kwargs))
    logging.info('Init db engine <%s> ok.' % hex(id(_DB_CTX)))


def connection():
    """
    Return _ConnectionCtx object that can be used by 'with' statement:
    with connection():
        pass
    """
    global _DB_CTX
    return ConnectionCtx(_DB_CTX)


def with_connection(func):
    """
    Decorator for reuse connection.
    @with_connection
    def foo(*args, **kw):
        f1()
        f2()
        f3()
    """

    global _DB_CTX

    @functools.wraps(func)
    def _wrapper(*args, **kw):
        with ConnectionCtx(_DB_CTX):
            return func(*args, **kw)

    return _wrapper


def transaction():
    """
    Create a transaction object so can use with statement:
    with transaction():
        pass
    >>> def update_profile(id, name, rollback):
    ...     u = dict(id=id, name=name, email='%s@test.org' % name, passwd=name, last_modified=time.time())
    ...     insert('user', **u)
    ...     r = update('update user set passwd=? where id=?', name.upper(), id)
    ...     if rollback:
    ...         raise StandardError('will cause rollback...')
    >>> with transaction():
    ...     update_profile(900301, 'Python', False)
    >>> select_one('select * from user where id=?', 900301).name
    u'Python'
    >>> with transaction():
    ...     update_profile(900302, 'Ruby', True)
    Traceback (most recent call last):
      ...
    StandardError: will cause rollback...
    >>> select('select * from user where id=?', 900302)
    []
    """
    global _DB_CTX
    return TransactionCtx(_DB_CTX)


def with_transaction(func):
    """
    A decorator that makes function around transaction.
    >>> @with_transaction
    ... def update_profile(id, name, rollback):
    ...     u = dict(id=id, name=name, email='%s@test.org' % name, passwd=name, last_modified=time.time())
    ...     insert('user', **u)
    ...     r = update('update user set passwd=? where id=?', name.upper(), id)
    ...     if rollback:
    ...         raise StandardError('will cause rollback...')
    >>> update_profile(8080, 'Julia', False)
    >>> select_one('select * from user where id=?', 8080).passwd
    u'JULIA'
    >>> update_profile(9090, 'Robert', True)
    Traceback (most recent call last):
      ...
    StandardError: will cause rollback...
    >>> select('select * from user where id=?', 9090)
    []
    """
    global _DB_CTX

    @functools.wraps(func)
    def _wrapper(*args, **kw):
        _start = time.time()
        with TransactionCtx(_DB_CTX):
            return func(*args, **kw)
        _profiling(_start)

    return _wrapper


def _select(sql, first, *args):
    """execute select SQL and return unique result or list results."""
    global _DB_CTX
    cursor = None
    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    sql = sql.replace('?', '%s')
    try:
        cursor = _DB_CTX.cursor()
        cursor.execute(sql, args)
        if cursor.description:
            names = [x[0] for x in cursor.description]
        if first:
            values = cursor.fetchone()
            if not values:
                return None
            return Dict(names, values)
        return [Dict(names, x) for x in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()


@with_connection
def get(sql, *args, **kwargs):
    """
    Execute select SQL and expected one int and only one int result.
    MultiColumnsError: Expect only one column.
    """
    global _DB_CTX
    cursor = None
    if kwargs:
        sql, args = _get_named_sql_args(sql, **kwargs)

    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    sql = sql.replace('?', '%s')
    try:
        cursor = _DB_CTX.cursor()
        cursor.execute(sql, args)
        values = cursor.fetchone()
        if len(values) == 1:
            return values[0]
        else:
            raise MultiColumnsError('Expect only one column.')
    finally:
        if cursor:
            cursor.close()


@with_connection
def select_one(sql, *args, **kwargs):
    """
    Execute select SQL and expected one result.
    If no result found, return None.
    If multiple results found, the first one returned.
    >>> u1 = dict(id=100, name='Alice', email='alice@test.org', passwd='ABC-12345', last_modified=time.time())
    >>> u2 = dict(id=101, name='Sarah', email='sarah@test.org', passwd='ABC-12345', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> insert('user', **u2)
    1
    >>> u = select_one('select * from user where id=?', 100)
    >>> u.name
    u'Alice'
    >>> select_one('select * from user where email=?', 'abc@email.com')
    >>> u2 = select_one('select * from user where passwd=? order by email', 'ABC-12345')
    >>> u2.name
    u'Alice'
    """
    if kwargs:
        sql, args = _get_named_sql_args(sql, **kwargs)
    return _select(sql, True, *args)


@with_connection
def select(sql, *args, **kwargs):
    """
    Execute select SQL and return list or empty list if no result.
    >>> u1 = dict(id=200, name='Wall.E', email='wall.e@test.org', passwd='back-to-earth', last_modified=time.time())
    >>> u2 = dict(id=201, name='Eva', email='eva@test.org', passwd='back-to-earth', last_modified=time.time())
    >>> insert('user', **u1)
    1
    >>> insert('user', **u2)
    1
    >>> L = select('select * from user where id=?', 900900900)
    >>> L
    []
    >>> L = select('select * from user where id=?', 200)
    >>> L[0].email
    u'wall.e@test.org'
    >>> L = select('select * from user where passwd=? order by id desc', 'back-to-earth')
    >>> L[0].name
    u'Eva'
    >>> L[1].name
    u'Wall.E'
    """
    if kwargs:
        sql, args = _get_named_sql_args(sql, **kwargs)
    return _select(sql, False, *args)


@with_connection
def _execute(sql, *args):
    global _DB_CTX
    cursor = None
    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    sql = sql.replace('?', '%s')
    try:
        cursor = _DB_CTX.connection.cursor()
        cursor.execute(sql, args)
        r = cursor.rowcount
        if _DB_CTX.transactions == 0:
            _DB_CTX.connection.commit()
        return r
    finally:
        if cursor:
            cursor.close()


def insert(table, **kwargs):
    """
    Execute insert SQL.
    IntegrityError: 1062 (23000): Duplicate entry '2000' for key 'PRIMARY'
    """
    cols, args = zip(*kwargs.items())
    sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
    return _execute(sql, *args)


def execute(sql, *args, **kwargs):
    """
    Execute SQL.
    """
    if kwargs:
        sql, args = _get_named_sql_args(sql, **kwargs)
    return _execute(sql, *args)


@with_connection
def batch_execute(sql, args: list):
    global _DB_CTX
    cursor = None
    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    sql = sql.replace('?', '%s')
    try:
        cursor = _DB_CTX.cursor()
        cursor.executemany(sql, args)
        r = cursor.rowcount
        if _DB_CTX.transactions == 0:
            _DB_CTX.connection.commit()
        return r
    finally:
        if cursor:
            cursor.close()


def get_connection():
    global _DB_CTX
    if not _DB_CTX.is_init():
        _DB_CTX.init()
    return _DB_CTX.connection


def prepare(prepared=True):
    global _DB_CTX
    _DB_CTX.prepared = prepared


def _get_named_sql_args(sql, **kwargs):
    args = [kwargs[r[1:]] for r in re.findall(_REGEX, sql)]
    return re.sub(_REGEX, '?', sql), args
