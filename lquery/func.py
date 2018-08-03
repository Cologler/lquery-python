# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# define some common functions for convert to SQL.
# ----------

from asq import query

NOT_QUERYABLE_FUNCS = []

def not_queryable(func):
    '''
    add the func into `NOT_QUERYABLE_FUNCS` list.

    that mean the result of func is not enumerable.
    '''
    NOT_QUERYABLE_FUNCS.append(func)
    return func

# not in ASQ

def to_memory(src):
    '''
    force load into memory.
    '''
    return src

# transforms

def select(src, selector):
    return query(src).select(selector)

def select_with_index(src, *args):
    return query(src).select_with_index(*args)

def select_with_correspondence(src, selector, *args):
    return query(src).select_with_correspondence(selector, *args)

def select_many(src, *args):
    return query(src).select_many(*args)

def select_many_with_index(src, *args):
    return query(src).select_many_with_index(*args)

def select_many_with_correspondence(src, *args):
    return query(src).select_many_with_correspondence(*args)

def group_by(src, *args):
    return query(src).group_by(*args)

# filter

def where(src, predicate):
    return query(src).where(predicate)

def of_type(src, classinfo):
    return query(src).of_type(classinfo)

def take(src, *args):
    return query(src).take(*args)

def take_while(src, predicate):
    return query(src).take_while(predicate)

def skip(src, *args):
    return query(src).skip(*args)

def skip_while(src, predicate):
    return query(src).skip_while(predicate)

def distinct(src, *args):
    return query(src).distinct(*args)

# sort

def order_by(src, *args):
    return query(src).order_by(*args)

def order_by_descending(src, *args):
    return query(src).order_by_descending(*args)

def reverse(src):
    return query(src).reverse()

# get one elements

@not_queryable
def default_if_empty(src, default):
    return query(src).default_if_empty(default)

@not_queryable
def first(src, *args):
    return query(src).first(*args)

@not_queryable
def first_or_default(src, default, *args):
    return query(src).first_or_default(default, *args)

@not_queryable
def last(src, *args):
    return query(src).last(*args)

@not_queryable
def last_or_default(src, default, *args):
    return query(src).last_or_default(default, *args)

@not_queryable
def single(src, *args):
    return query(src).single(*args)

@not_queryable
def single_or_default(src, default, *args):
    return query(src).single_or_default(default, *args)

@not_queryable
def element_at(src, index):
    return query(src).element_at(index)

# get queryable props

@not_queryable
def count(src, *args):
    return query(src).count(*args)

# two collection operations

def concat(src, other):
    return query(src).concat(other)

def difference(src, other, *args):
    return query(src).difference(other, *args)

def intersect(src, other, *args):
    return query(src).intersect(other, *args)

def union(src, other, *args):
    return query(src).union(other, *args)

def join(src, inner_iterable, *args):
    return query(src).join(inner_iterable, *args)

def group_join(src, inner_iterable, *args):
    return query(src).group_join(inner_iterable, *args)

def zip(src, other, *args):
    return query(src).zip(other, *args)

# for numbers

@not_queryable
def min(src, *args):
    return query(src).min(*args)

@not_queryable
def max(src, *args):
    return query(src).max(*args)

# aggregates

@not_queryable
def sum(src, *args):
    return query(src).sum(*args)

@not_queryable
def average(src, *args):
    return query(src).average(*args)

@not_queryable
def aggregate(src, reducer, seed, result_selector):
    return query(src).aggregate(reducer, seed, result_selector)

# logic operations

@not_queryable
def any(src, *args):
    return query(src).any(*args)

@not_queryable
def all(src, *args):
    return query(src).all(*args)

@not_queryable
def contains(src, value, *args):
    return query(src).contains(value, *args)

@not_queryable
def sequence_equal(src, other, *args):
    return query(src).sequence_equal(other, *args)
