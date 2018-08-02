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


QUERY_CLS = MongoDbQuery


class FakeCollection:
    '''a simple fake collection class for detect SQL convert result.'''

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


class TestMongoDbGettingStartedExamples(unittest.TestCase):
    # test examples from https://docs.mongodb.com/manual/tutorial/getting-started/

    def test_query_select_all_documents(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.to_list()
        self.assertDictEqual(fc.filter, {})

    def test_query_select_documents_by_predicate(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['status'] == 'D').to_list()
        self.assertDictEqual(fc.filter, { 'status': 'D' })

    def test_query_match_an_embedded_document(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['size'] == { 'h': 14, 'w': 21, 'uom': 'cm' }).to_list()
        self.assertDictEqual(fc.filter, { 'size': { 'h': 14, 'w': 21, 'uom': 'cm' } })

    def test_query_match_a_field_in_an_embedded_document(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['size']['uom'] == 'in').to_list()
        self.assertDictEqual(fc.filter, { "size.uom": "in" })

    def test_query_match_an_element_in_an_array(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: 'item' in x['list']).to_list()
        self.assertDictEqual(fc.filter, { 'list': 'item' })

    def test_query_match_an_array_exactly(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['tags'] == ["red", "blank"] ).to_list()
        self.assertDictEqual(fc.filter, { 'tags': ["red", "blank"] })


class TestMongoDbWhereFieldEq(unittest.TestCase):

    def test_query_select_documents_by_eq(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['status'] == 'D').to_list()
        self.assertDictEqual(fc.filter, { 'status': 'D' })

    def test_query_select_documents_by_eq_reversed(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: 'D' == x['status']).to_list()
        self.assertDictEqual(fc.filter, { 'status': 'D' })


class TestMongoDbWhereFieldEqDoc(unittest.TestCase):

    def test_query_select_documents_by_doc(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['size'] == {'h': 14, 'w': 21, 'uom': 'cm'}).to_list()
        self.assertDictEqual(fc.filter, {'size': {'h': 14, 'w': 21, 'uom': 'cm'}})

    def test_query_select_documents_by_doc_ref(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        obj = { 'h': 14, 'w': 21, 'uom': 'cm' }
        mongo_query.where(lambda x: x['size'] == obj).to_list()
        self.assertDictEqual(fc.filter, { 'size': obj })

    def test_query_select_documents_by_doc_dict(self):
        # arguments of dict not use `x`, we can call it in `where()` !
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['size'] == dict(h=14, w=21, uom='cm')).to_list()
        self.assertDictEqual(fc.filter, {'size': {'h': 14, 'w': 21, 'uom': 'cm'}})

    def test_query_select_documents_by_doc_func(self):
        def func(h, w, uom):
            return dict(h=h, w=w, uom=uom)
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['size'] == func(14, 21, 'cm')).to_list()
        self.assertDictEqual(fc.filter, {'size': {'h': 14, 'w': 21, 'uom': 'cm'}})


class TestMongoDbWhereFieldIn(unittest.TestCase):

    def test_query_select_documents_by_in(self):
        '''
        The $in operator selects the documents where the value of a field equals any value in the specified array.

        match `x['status']` equals `A` or `x['status']` equals `B`
        '''
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['status'] in ['A', 'B']).to_list()
        # x['status'] in ['A', 'B', 'C'] mean:
        self.assertDictEqual(fc.filter, { 'status': { '$in': ['A', 'B'] } })

    def test_query_select_documents_by_in_reversed(self):
        '''
        match one element of `x['status']` equals `A`
        '''
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: 'D' in x['status']).to_list()
        self.assertDictEqual(fc.filter, { 'status': 'D' })


class TestMongoDbQuery(unittest.TestCase):
    def test_take(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.take(1).to_list()
        self.assertEqual(fc.limit, 1)

    def test_take_reduce_1(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.take(10).take(5).to_list()
        self.assertEqual(fc.limit, 5)

    def test_take_reduce_2(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.take(5).take(10).to_list()
        self.assertEqual(fc.limit, 5)

    def test_skip(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.skip(1).to_list()
        self.assertEqual(fc.skip, 1)

    def test_skip_reduce(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.skip(1).skip(4).to_list()
        self.assertEqual(fc.skip, 5)

    def test_query_field_greater_than(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['name'] > 1).to_list()
        self.assertDictEqual(fc.filter, { 'name': { '$gt': 1 } })

    def test_query_field_less_than(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['name'] < 1).to_list()
        self.assertDictEqual(fc.filter, { 'name': { '$lt': 1 } })

    def test_query_embedded_doc_field_multi_where(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: x['size']['h'] == 14).where(lambda x: x['size']['uom'] == 'cm').to_list()
        self.assertDictEqual(fc.filter, { 'size.h': 14, 'size.uom': "cm" })

    def test_query_embedded_doc_field_with_and(self):
        fc = FakeCollection()
        mongo_query = QUERY_CLS(fc)
        mongo_query.where(lambda x: (x['size']['h'] == 14) & (x['size']['uom'] == 'cm')).to_list()
        self.assertDictEqual(fc.filter, { 'size.h': 14, 'size.uom': "cm" })


class TestMongoDbReduce(unittest.TestCase):
    def test_get_reduce_info(self):
        mongo_query = QUERY_CLS(None) # get reduce info does not require a valid collection.
        reduce_info = mongo_query\
            .where(lambda x: (x['size']['h'] == 14) & (x['size']['uom'] == 'cm'))\
            .skip(1)\
            .where(lambda x: x['size']['w'] > 15)\
            .get_reduce_info()
        self.assertEqual(reduce_info.mode, reduce_info.MODE_NORMAL)
        self.assertListEqual(
            [x.type for x in reduce_info.details],
            [reduce_info.TYPE_SQL, reduce_info.TYPE_SQL, reduce_info.TYPE_MEMORY]
        )

    def test_reduce_with_take_0_in_sql(self):
        mongo_query = QUERY_CLS(None)
        reduce_info = mongo_query\
            .where(lambda x: (x['size']['h'] == 14) & (x['size']['uom'] == 'cm'))\
            .skip(1)\
            .take(0)\
            .where(lambda x: x['size']['w'] > 15)\
            .get_reduce_info()
        self.assertEqual(reduce_info.mode, reduce_info.MODE_EMPTY)
        self.assertListEqual(
            [x.type for x in reduce_info.details],
            [reduce_info.TYPE_NOT_EXEC] * 4
        )

    def test_reduce_with_take_0_in_memory(self):
        # take(0) in memory is not be reduce since user can do something in lambda.
        mongo_query = QUERY_CLS(None)
        reduce_info = mongo_query\
            .where(lambda x: (x['size']['h'] == 14) & (x['size']['uom'] == 'cm'))\
            .skip(1)\
            .where(lambda x: x['size']['w'] > 15)\
            .take(0)\
            .get_reduce_info()
        self.assertEqual(reduce_info.mode, reduce_info.MODE_NORMAL)
        self.assertListEqual(
            [x.type for x in reduce_info.details],
            [reduce_info.TYPE_SQL, reduce_info.TYPE_SQL, reduce_info.TYPE_MEMORY, reduce_info.TYPE_MEMORY]
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
