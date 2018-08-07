# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys
import traceback
import unittest
import itertools

import pytest

from lquery import enumerable
from lquery.funcs import LinqQuery

def query1() -> LinqQuery:
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

def query2() -> LinqQuery:
    return enumerable([1, 2, 3, 4, 5, 6])

def test_method_select():
    items = query1().select(lambda x: x['name']).to_list()
    assert items == ['x', 'y', 'y', 'ys']

def test_method_select_many():
    items = query1().select_many(lambda x: x.values()).to_list()
    assert items == ['x', '3', 'y', '2', 'y', '3', 'ys', '3g', 'spec-value']

def test_method_group_by():
    # TODO: add test
    pass

def test_method_where():
    items = query1().where(lambda x: 'spec-key' in x).to_list()
    assert items == [{'name': 'ys', 'value': '3g', 'spec-key': 'spec-value'}]

def test_method_of_type():
    query: Queryable = enumerable([1, '1', b's'])
    assert query.of_type(str).to_list() == ['1']

def test_method_take():
    assert query2().take(2).to_list() == [1, 2]

def test_method_take_while():
    assert query2().take_while(lambda x: x < 3).to_list() == [1, 2]

def test_method_skip():
    assert query2().skip(1).to_list() == [2, 3, 4, 5, 6]

def test_method_skip_while():
    assert query2().skip_while(lambda x: x < 3).to_list() == [3, 4, 5, 6]

def test_method_distinct():
    assert enumerable([1, 2, 3, 4, 3, 4]).distinct().to_list() == [1, 2, 3, 4]

def test_method_order_by():
    assert enumerable([3, 4, 1, 2]).order_by().to_list() == [1, 2, 3, 4]

def test_method_order_by_descending():
    assert enumerable([3, 4, 1, 2]).order_by_descending().to_list() == [4, 3, 2, 1]

def test_method_reverse():
    assert enumerable([1, 2, 3, 4, 3, 4]).reverse().to_list() == [4, 3, 4, 3, 2, 1]

def test_method_first():
    assert enumerable([1]).first() == 1

    with pytest.raises(ValueError):
        enumerable([]).first()

    assert enumerable([1, 2, 3, 4, 3, 4]).first(lambda x: x > 3) == 4


def test_method_first_or_default():
    assert enumerable([]).first_or_default(1) == 1

def test_method_last():
    pass

def test_method_last_or_default():
    pass

def test_method_single():
    pass

def test_method_single_or_default():
    pass

def test_method_element_at():
    assert enumerable([2, 5, 7, 'f']).element_at(0) == 2
    assert enumerable([2, 5, 7, 'f']).element_at(1) == 5
    with pytest.raises(IndexError):
        enumerable([]).element_at(0)

    # also support less then zero:
    assert enumerable([2, 5, 7, 'f']).element_at(-1) == 'f'

def test_method_count():
    pass

def test_method_concat():
    pass

def test_method_difference():
    pass

def test_method_intersect():
    pass

def test_method_union():
    pass

def test_method_join():
    pass

def test_method_group_join():
    pass

def test_method_zip():
    src_1 = [2, 5, 7, 'f']
    src_2 = ['f', 8, 49, 'fgg']
    src_3 = [3, 4, 5]
    src_4 = ['fds', 'uy']

    query = enumerable(src_1)

    with pytest.raises(TypeError):
        query.zip()

    assert query.zip(src_2).to_list() == list(zip(src_1, src_2))
    assert query.zip(src_2, src_3).to_list() == list(zip(src_1, src_2, src_3))
    assert query.zip(src_2, src_3, src_4).to_list() == list(zip(src_1, src_2, src_3, src_4))

def test_method_zip_longest():
    src_1 = [2, 5, 7, 'f']
    src_2 = ['f', 8, 49, 'fgg']
    src_3 = [3, 4, 5]
    src_4 = ['fds', 'uy']

    with pytest.raises(TypeError):
        enumerable(src_1).zip_longest()

    with pytest.raises(TypeError):
        enumerable(src_1).zip_longest(fill_value=None)

    assert enumerable(src_1).zip_longest(src_2).to_list() ==\
        list(itertools.zip_longest(src_1, src_2, fillvalue=None))
    assert enumerable(src_1).zip_longest(src_2, src_3).to_list() ==\
        list(itertools.zip_longest(src_1, src_2, src_3, fillvalue=None))
    assert enumerable(src_1).zip_longest(src_2, src_3, src_4).to_list() ==\
        list(itertools.zip_longest(src_1, src_2, src_3, src_4, fillvalue=None))

    assert enumerable(src_1).zip_longest(src_2, fill_value=8).to_list() ==\
        list(itertools.zip_longest(src_1, src_2, fillvalue=8))
    assert enumerable(src_1).zip_longest(src_2, src_3, fill_value=8).to_list() ==\
        list(itertools.zip_longest(src_1, src_2, src_3, fillvalue=8))
    assert enumerable(src_1).zip_longest(src_2, src_3, src_4, fill_value=8).to_list() ==\
        list(itertools.zip_longest(src_1, src_2, src_3, src_4, fillvalue=8))

def test_method_min():
    items = [1, 8, 15]
    assert enumerable(items).min() == min(items)

    with pytest.raises(TypeError):
        enumerable([1, '3']).min()

    assert enumerable([1, '3']).min(int) == min([1, 3])

def test_method_max():
    items = [1, 8, 15]
    assert enumerable(items).max() == max(items)

    with pytest.raises(TypeError):
        enumerable([1, '3']).max()

    assert enumerable([1, '3']).max(int) == max([1, 3])

def test_method_sum():
    items = [1, 8, 15]
    assert enumerable(items).sum() == sum(items)

    with pytest.raises(TypeError):
        enumerable([1, '3']).sum()

    assert enumerable([1, '3']).sum(int) == sum([1, 3])


def test_method_average():
    pass

def test_method_aggregate():
    pass

def test_method_any():
    # should return `True` if `IQueryable` is not empty.
    assert enumerable([]).any() is False
    assert enumerable([False]).any() is True
    assert enumerable([True]).any() is True

    # if `predicate` exists,
    # should return `True` if has any items is `True`
    assert enumerable([]).any(lambda x: True) is False
    assert enumerable([False]).any(lambda x: True) is True
    assert enumerable([True]).any(lambda x: False) is False

def test_method_all():
    # should return `True` if all items are `True`
    assert enumerable([]).all() is True
    assert enumerable([False]).all() is False
    assert enumerable([True]).any() is True

def test_method_contains():
    assert enumerable([1, 2, 4, 6, 3, 1, 2]).contains(3) is True
    assert enumerable([1, 2, 4, 6, 3, 1, 2]).contains(30) is False

def test_method_sequence_equal():
    pass

def test_method_to_list():
    assert query1().to_list() == list(query1())

def test_method_to_dict():
    pass

def test_method_for_each():
    data = {
        'value': 0
    }
    query = enumerable([1, 2, 4, 6, 3, 1, 2])
    def cb(x):
        data['value'] += x
    assert query.for_each(cb) is None
    assert sum([1, 2, 4, 6, 3, 1, 2]) == data['value']

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
