# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the IQueryable for SQLite.
# ----------

import sqlite3
import itertools

from ..expr import Make
from ..queryable import AbstractQueryable, IQueryProvider
from ..iterable import IterableQueryProvider

from ._common import new

class SQLiteQueryable(AbstractQueryable):

    def __init__(self, connection, table_name: str):
        super().__init__(Make.ref(self), PROVIDER)
        self._connection = connection
        self._table_name = table_name

    def get_sqlstr(self):
        return f'SELECT * FROM {self._table_name}'

    def get_sqlargs(self):
        return ()

    def __iter__(self):
        cursor = self._connection.cursor()
        reader = cursor.execute(self.get_sqlstr(), self.get_sqlargs())
        col_names = [desc[0] for desc in reader.description]
        for row in cursor.execute(self.get_sqlstr()):
            yield new(**dict(zip(col_names, row)))

    @staticmethod
    def from_strings(connect_str, table_name):
        conn = sqlite3.connect(connect_str)
        return SQLiteQueryable(conn, table_name)


class SQLiteQueryProvider(IterableQueryProvider):
    pass

PROVIDER = SQLiteQueryProvider()

class SQLiteTable:
    def __init__(self, connection, name: str):
        self._connection = connection
        self._name = name
        self._cols = None

    def _get_cols(self):
        if self._cols is None:
            cursor = self._connection.cursor()
            reader = cursor.execute(f'SELECT * FROM {self._name}')
            self._cols = tuple(desc[0] for desc in reader.description)
        return self._cols

    def insert(self, record):
        self.insert_many([record])

    def insert_many(self, records: list):
        cols = self._get_cols()
        args = []
        for record in records:
            data = vars(record)
            args.append([data.get(c) for c in cols])
        cursor = self._connection.cursor()
        param = ','.join(['?'] * len(cols))
        sql = f'INSERT INTO {self._name} VALUES ({param})'
        cursor.executemany(sql, args)
        self._connection.commit()

    def query(self):
        return SQLiteQueryable(self._connection, self._name)


class SQLiteDbContext:
    def __init__(self, connection):
        self._connection = connection

    def table(self, name):
        '''
        get the `SQLiteTable`.
        '''
        return SQLiteTable(self._connection, name)
