# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
import traceback
import unittest

from lquery.iterable import IterableQuery
from lquery.extras.mongodb import MongoDbQuery

import lquery.expr_builder as expr_builder
expr_builder.DEBUG = False

raw_query = IterableQuery([
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

    def find(self, filter=None, *args, **kwargs):
        self.filter = filter
        return self._items[:]

class TestMongoDbQuery(unittest.TestCase):
    def test_field_equal(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.where(lambda x: x['name'] == 1).to_list()
        self.assertDictEqual(fc.filter, { 'name': 1 })

    def test_field_greater_than(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.where(lambda x: x['name'] > 1).to_list()
        self.assertDictEqual(fc.filter, { 'name': { '$gt': 1 } })

    def test_field_less_than(self):
        fc = FakeCollection()
        mongo_query = MongoDbQuery(fc)
        mongo_query.where(lambda x: x['name'] < 1).to_list()
        self.assertDictEqual(fc.filter, { 'name': { '$lt': 1 } })


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        unittest.main()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
