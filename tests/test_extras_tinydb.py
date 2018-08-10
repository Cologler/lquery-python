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

from tinydb import TinyDB
from tinydb.storages import MemoryStorage
from lquery.extras.tinydb import TinyDbQuery, patch

def get_example_db_1():
    db = TinyDB(storage=MemoryStorage)
    table = db.table()
    table.insert({'int': 1, 'char': 'a'})
    table.insert({'int': 1, 'char': 'b'})
    table.insert({'int': 2, 'char': 'b'})
    return db

def get_example_db_2():
    db = TinyDB(storage=MemoryStorage)
    table = db.table()
    table.insert({'int': 1, 'char': 'a', 'dict': {
        'key': 1
    }})
    table.insert({'int': 1, 'char': 'b', 'dict': {
        'key': 2
    }})
    table.insert({'int': 2, 'char': 'b', 'dict': {
        'key': 2
    }})
    return db

def test_get_items_by_index():
    db = get_example_db_1()
    table = db.table()
    query = TinyDbQuery(table)
    # field 1
    assert query.where(lambda x: x['int'] == 1).to_list() == [
        {'int': 1, 'char': 'a'},
        {'int': 1, 'char': 'b'}
    ]
    # field 2
    assert query.where(lambda x: x['char'] == 'b').to_list() == [
        {'int': 1, 'char': 'b'},
        {'int': 2, 'char': 'b'}
    ]

def test_get_items_by_index_with_attrstyle():
    db = get_example_db_1()
    table = db.table()
    query = TinyDbQuery(table)
    # provider was rewrite bytecode and change `int` to `['int']`!
    assert query.where(lambda x: x.int == 1).to_list() == [
        {'int': 1, 'char': 'a'},
        {'int': 1, 'char': 'b'}
    ]

def test_get_items_by_doc_id():
    db = get_example_db_1()
    table = db.table()
    query = TinyDbQuery(table)
    assert query.where(lambda x: x.doc_id == 2).to_list() == [{'int': 1, 'char': 'b'}]
    assert query.where(lambda x: x.doc_id == 8).to_list() == []

def test_get_items_by_index_which_not_exists():
    db = get_example_db_1()
    table = db.table()
    query = TinyDbQuery(table)
    assert query.where(lambda x: x['some-not-exists-field'] == 1).to_list() == []

def test_get_items_by_index_which_not_exists_with_attrstyle():
    db = get_example_db_1()
    table = db.table()
    query = TinyDbQuery(table)
    assert query.where(lambda x: x.some_not_exists_field == 1).to_list() == []

def test_get_items_by_index_deep():
    db = get_example_db_2()
    table = db.table()
    query = TinyDbQuery(table)

    assert query.where(lambda x: x['dict']['key'] == 1).to_list() == [
        {'int': 1, 'char': 'a', 'dict': {'key': 1}}
    ]
    assert query.where(lambda x: x['dict']['key_not_exists'] == 1).to_list() == []
    assert query.where(lambda x: x['key_not_exists']['dict'] == 1).to_list() == []

    with pytest.raises(TypeError):
        # TypeError: argument of type 'int' is not iterable
        # user should know `x['int']` is not a dict.
        # I don't want call `isinstance` for each times.
        assert query.where(lambda x: x['int']['dict'] == 1).to_list() == []

def test_get_items_by_attr_deep():
    db = get_example_db_2()
    table = db.table()
    query = TinyDbQuery(table)

    assert query.where(lambda x: x.dict.key == 1).to_list() == [
        {'int': 1, 'char': 'a', 'dict': {'key': 1}}
    ]
    assert query.where(lambda x: x.dict.key_not_exists == 1).to_list() == []
    assert query.where(lambda x: x.key_not_exists.dict == 1).to_list() == []

    with pytest.raises(AttributeError):
        # x.doc_id.key will not convert to x.doc_id['key']
        # so here raise `AttributeError` instead of `KeyError`
        assert query.where(lambda x: x.doc_id.key_not_exists == 1).to_list() == []

def test_get_items_by_in():
    db = TinyDB(storage=MemoryStorage)
    table = db.table()
    table.insert({'int': 1})
    table.insert({'char': 'a'})
    table.insert({'str': 'ab'})
    table.insert({'dict': {'key': 1}})
    table.insert({'list': ['item']})

    query = TinyDbQuery(table)

    with pytest.raises(TypeError):
        query.where(lambda x: 'a' in x.int).to_list()

    assert query.where(lambda x: 'a' in x.char).to_list() == [
        {'char': 'a'}
    ]
    assert query.where(lambda x: 'a' in x.str).to_list() == [
        {'str': 'ab'}
    ]
    assert query.where(lambda x: 'key' in x.dict).to_list() == [
        {'dict': {'key': 1}}
    ]
    assert query.where(lambda x: 'key-some' in x.dict).to_list() == []
    assert query.where(lambda x: 'item' in x.list).to_list() == [
        {'list': ['item']}
    ]
    assert query.where(lambda x: 'item-some' in x.list).to_list() == []

def test_patch():
    db = get_example_db_1()
    table = db.table()
    assert not hasattr(table, 'query')
    patch()
    assert hasattr(table, 'query')
    query = table.query()
    assert isinstance(query, TinyDbQuery)
    assert query.where(lambda x: x['int'] == 1).to_list() == [
        {'int': 1, 'char': 'a'},
        {'int': 1, 'char': 'b'}
    ]
