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
        item = items[0]
        self.assertDictEqual(item, {'name': 'ys', 'value': '3g', 'spec-key': 'spec-value'})

    def test_where_2(self):
        for item in query().where(lambda x: x['name'] == 'y').take(1):
            self.assertEqual(item['name'], 'y')

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        unittest.main()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
