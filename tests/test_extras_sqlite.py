# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# test for sqlite
# ----------

import sqlite3

from lquery.extras.sqlite import new, SQLiteDbContext

def test_sqlite():
    conn = sqlite3.connect(':memory:')
    context = SQLiteDbContext(conn)
    c = conn.cursor()
    c.execute('CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)')
    conn.commit()
    table = context.table('stocks')
    table.insert(new(trans='BUY2', date='2016-01-05'))
    table.insert_many([
        new(trans='BUY1', date='2018-01-05', symbol='cnn'),
        new(date='2017-01-05', trans='BUY2')
    ])
    assert len(table.query().to_list()) == 3
    query = table.query().where(lambda x: x.trans == 'BUY2').select(lambda x: x.date)
    assert set(query) == set(['2016-01-05', '2017-01-05'])
