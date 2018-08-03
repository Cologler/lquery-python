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

def get_memory_db():
    return TinyDB(storage=MemoryStorage)

class Test(unittest.TestCase):
    def test_simple(self):
        db = get_memory_db()
        table = db.table()
        table.insert({'int': 1, 'char': 'a'})
        table.insert({'int': 1, 'char': 'b'})
        query = TinyDbQuery(table)
        self.assertListEqual(
            query.where(lambda x: x['int'] == 1).to_list(),
            [{'int': 1, 'char': 'a'}, {'int': 1, 'char': 'b'}]
        )
        self.assertListEqual(
            query.where(lambda x: x['char'] == 'b').to_list(),
            [{'int': 1, 'char': 'b'}]
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
