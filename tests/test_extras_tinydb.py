# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
import traceback
import unittest

from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from lquery.extras.tinydb import TinyDbQuery

def get_example_db():
    db = TinyDB(storage=MemoryStorage)
    table = db.table()
    table.insert({'int': 1, 'char': 'a'})
    table.insert({'int': 1, 'char': 'b'})
    table.insert({'int': 2, 'char': 'b'})
    return db

class Test(unittest.TestCase):
    def test_by_field_1_indexstyle(self):
        db = get_example_db()
        table = db.table()
        query = TinyDbQuery(table)
        self.assertListEqual(
            query.where(lambda x: x['int'] == 1).to_list(),
            [{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]
        )

    def test_by_field_2_indexstyle(self):
        db = get_example_db()
        table = db.table()
        query = TinyDbQuery(table)
        self.assertListEqual(
            query.where(lambda x: x['char'] == 'b').to_list(),
            [{'int': 1, 'char': 'b'}, {'int': 2, 'char': 'b'}]
        )

    def test_by_doc_id(self):
        db = get_example_db()
        table = db.table()
        query = TinyDbQuery(table)
        self.assertListEqual(
            query.where(lambda x: x.doc_id == 2).to_list(),
            [{'int': 1, 'char': 'b'}]
        )

    def test_by_field_1_attrstyle(self):
        # provider was rewrite bytecode and change `int` to `['int']` !
        db = get_example_db()
        table = db.table()
        query = TinyDbQuery(table)
        self.assertListEqual(
            query.where(lambda x: x.int == 1).to_list(),
            [{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]
        )

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        unittest.main()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
