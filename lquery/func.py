# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from asq import query

def to_memory(src):
    return src

def where(src, predicate):
    return query(src).where(predicate)

def select(src, selector):
    return query(src).select(selector)

def take(src, count):
    return query(src).take(count)

def skip(src, count):
    return query(src).skip(count)
