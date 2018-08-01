# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# define some common functions for convert to SQL.
# ----------

from asq import query

def to_memory(src):
    '''
    force load into memory.
    '''
    return src

def where(src, predicate):
    return query(src).where(predicate)

def select(src, selector):
    return query(src).select(selector)

def select_many(src, collection_selector, result_selector):
    return query(src).select_many(
        collection_selector=collection_selector,
        result_selector=result_selector)

def take(src, count):
    return query(src).take(count)

def skip(src, count):
    return query(src).skip(count)
