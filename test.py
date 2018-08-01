# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
import traceback
import unittest

from lquery import enumerable
from lquery.extras.mongodb import MongoDbQuery

from lquery.expr_builder import debug as expr_debug

raw_query = enumerable([
    {
        'name': 'x',
        'value': '3',
    }, {
        'name': 'y',
        'value': '2',
    }, {
        'name': 'y',
        'value': '3',
    },
])

class TestIterableQuery(unittest.TestCase):
    def test_to_str(self):
        for item in raw_query.where(lambda x: x['name'] == 'y').take(1):
            self.assertEqual(item['name'], 'y')

class FakeCollection:
    def __init__(self, items=[]):
        self._items = items
        self.filter = None
        self.projection = None
        self.skip = None
        self.limit = None

    def find(self, filter=None, projection=None, skip=0, limit=0, sort=None):
        self.filter = filter
        self.projection = projection
        self.skip = skip
        self.limit = limit
        return self._items[:]

class TestMongoDbQuery(unittest.TestCase):
    def test_take(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.take(1).to_list()
        self.assertEqual(fc.limit, 1)

    def test_take_reduce_1(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.take(10).take(5).to_list()
        self.assertEqual(fc.limit, 5)

    def test_take_reduce_2(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.take(5).take(10).to_list()
        self.assertEqual(fc.limit, 5)

    def test_skip(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.skip(1).to_list()
        self.assertEqual(fc.skip, 1)

    def test_skip_reduce(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.skip(1).skip(4).to_list()
        self.assertEqual(fc.skip, 5)

    def test_query_field_greater_than(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.where(lambda x: x['name'] > 1).to_list()
        self.assertDictEqual(fc.filter, { 'name': { '$gt': 1 } })

    def test_query_field_less_than(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.where(lambda x: x['name'] < 1).to_list()
        self.assertDictEqual(fc.filter, { 'name': { '$lt': 1 } })

    def test_query_all(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.to_list()
        self.assertDictEqual(fc.filter, {})

    def test_query_field_equal(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.where(lambda x: x['status'] == 'D').to_list()
        self.assertDictEqual(fc.filter, { 'status': 'D' })

    def test_query_embedded_doc(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.where(lambda x: x['size']['h'] == 14).to_list()
        self.assertDictEqual(fc.filter, { 'size': { 'h': 14 } })

    def test_query_embedded_doc_multi_where(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.where(lambda x: x['size']['h'] == 14).where(lambda x: x['size']['uom'] == 'cm').to_list()
        self.assertDictEqual(fc.filter, { 'size': { 'h': 14, 'uom': "cm" } })

    def test_query_embedded_doc_with_and(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.where(lambda x: (x['size']['h'] == 14) & (x['size']['uom'] == 'cm')).to_list()
        self.assertDictEqual(fc.filter, { 'size': { 'h': 14, 'uom': "cm" } })


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        unittest.main()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
