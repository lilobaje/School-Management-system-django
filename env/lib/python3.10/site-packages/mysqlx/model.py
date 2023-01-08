import logging
import threading


class DBCtx(threading.local):
    """
    Thread local object that holds connection info.
    """

    def __init__(self, connect):
        self.connect = connect
        self.connection = None
        self.transactions = 0
        self.prepared = True

    def is_init(self):
        return self.connection is not None

    def init(self):
        self.transactions = 0
        self.connection = self.connect()
        logging.debug('use connection <%s>...' % hex(id(self.connection)))

    def release(self):
        if self.connection:
            logging.debug('release connection <%s>...' % hex(id(self.connection)))
            self.connection.close()
            self.connection = None

    def cursor(self):
        """
        Return cursor
        """
        logging.debug('cursor prepared: %s' % self.prepared)
        return self.connection.cursor(prepared=self.prepared)

    def statement(self, sql):
        """
        Return statement
        """
        return self.connection.statement(sql)


class ConnectionCtx(object):
    """
    ConnectionCtx object that can open and close connection context. _ConnectionCtx object can be nested and only the most
    outer connection has effect.
    with connection():
        pass
        with connection():
            pass
    """

    def __init__(self, db_ctx):
        self.db_ctx = db_ctx

    def __enter__(self):
        self.should_cleanup = False
        if not self.db_ctx.is_init():
            self.db_ctx.init()
            self.should_cleanup = True
        return self

    def __exit__(self, exctype, excvalue, traceback):
        if self.should_cleanup:
            self.db_ctx.release()


class TransactionCtx(object):
    """
    TransactionCtx object that can handle transactions.
    with TransactionCtx():
        pass
    """

    def __init__(self, db_ctx):
        self.db_ctx = db_ctx

    def __enter__(self):
        self.should_close_conn = False
        if not self.db_ctx.is_init():
            # needs open a connection first:
            self.db_ctx.init()
            self.should_close_conn = True
        self.db_ctx.transactions = self.db_ctx.transactions + 1
        logging.info('begin transaction...' if self.db_ctx.transactions == 1 else 'join current transaction...')
        return self

    def __exit__(self, exctype, excvalue, traceback):
        self.db_ctx.transactions -= 1
        try:
            if self.db_ctx.transactions == 0:
                if exctype is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            if self.should_close_conn:
                self.db_ctx.release()

    def commit(self):
        logging.info('commit transaction...')
        try:
            self.db_ctx.connection.commit()
            logging.info('commit ok.')
        except Exception:
            logging.warning('commit failed. try rollback...')
            self.db_ctx.connection.rollback()
            logging.warning('rollback ok.')
            raise

    def rollback(self):
        logging.warning('rollback transaction...')
        self.db_ctx.connection.rollback()
        logging.info('rollback ok.')


class DBError(Exception):
    pass


class MultiColumnsError(DBError):
    pass


class Dict(dict):
    """
    Simple dict but support access as x.y style.
    >>> d1 = Dict()
    >>> d1['x'] = 100
    >>> d1.x
    100
    >>> d1.y = 200
    >>> d1['y']
    200
    >>> d2 = Dict(a=1, b=2, c='3')
    >>> d2.c
    '3'
    >>> d2['empty']
    Traceback (most recent call last):
        ...
    KeyError: 'empty'
    >>> d2.empty
    Traceback (most recent call last):
        ...
    AttributeError: 'Dict' object has no attribute 'empty'
    >>> d3 = Dict(('a', 'b', 'c'), (1, 2, 3))
    >>> d3.a
    1
    >>> d3.b
    2
    >>> d3.c
    3
    """

    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


class SqlModel:

    def __init__(self, sql, dynamic=False, include=None):
        self.sql = sql
        self.dynamic = dynamic
        self.include = include

