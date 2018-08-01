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

def query():
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
        items = query().where(lambda x: 'spec-key' in x).to_list()
        self.assertEqual(len(items), 1)
        self.assertDictEqual(items[0], {'name': 'ys', 'value': '3g', 'spec-key': 'spec-value'})

    def test_select(self):
        items = query().select(lambda x: x['name']).to_list()
        self.assertListEqual(items, ['x', 'y', 'y', 'ys'])

    def test_select_many(self):
        items = query().select_many(lambda x: x.values()).to_list()
        self.assertListEqual(items, ['x', '3', 'y', '2', 'y', '3', 'ys', '3g', 'spec-value'])

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        unittest.main()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
