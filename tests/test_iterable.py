# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
import traceback
import unittest

import pytest

from lquery import enumerable

def query1():
    return enumerable([
        {
            'name': 'x',
            'value': '3',
        }, {
            'name': 'y',
            'value': '2',
        }, {
            'name': 'y',
            'value': '3',
        }, {
            'name': 'ys',
            'value': '3g',
            'spec-key': 'spec-value'
        },
    ])

class TestIterableQuery(unittest.TestCase):
    def test_where(self):
        items = query1().where(lambda x: 'spec-key' in x).to_list()
        self.assertEqual(len(items), 1)
        self.assertDictEqual(items[0], {'name': 'ys', 'value': '3g', 'spec-key': 'spec-value'})

    def test_select_many(self):
        items = query1().select_many(lambda x: x.values()).to_list()
        self.assertListEqual(items, ['x', '3', 'y', '2', 'y', '3', 'ys', '3g', 'spec-value'])

def test_method_load():
    items = query1().load()
    assert list(items) == list(items)

def test_select():
    items = query1().select(lambda x: x['name']).to_list()
    assert items == ['x', 'y', 'y', 'ys']

def test_method_where():
    items = query1().where(lambda x: 'spec-key' in x).to_list()
    assert items == [{'name': 'ys', 'value': '3g', 'spec-key': 'spec-value'}]

def test_method_to_list():
    query = query1().where(lambda x: 'spec-key' in x)
    assert list(query) == query.to_list()

def test_not_exists_method():
    # ensure not recursive
    with pytest.raises(AttributeError):
        query1().some_not_exists_method()


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        unittest.main()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
