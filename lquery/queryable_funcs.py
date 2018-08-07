# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# define some common extension functions for convert to SQL.
# ----------

from typing import Callable, Set, Dict, List, TypeVar

from asq import query
from asq.selectors import identity
from asq.namedelements import IndexedElement, KeyedElement

from .queryable import IQueryable

# element
T = TypeVar('T')
# element of other collection
T2 = TypeVar('T2')
# result selector
TR = TypeVar('TR')
# key selector
TK = TypeVar('TK')
# value selector
TV = TypeVar('TV')

# not in ASQ

def to_memory(src):
    '''
    force load into memory.
    '''
    return src

# transforms

@IQueryable.extend_linq(True)
def select(src, selector):
    return query(src).select(selector)

@IQueryable.extend_linq(True)
def select_with_index(src, *args):
    return query(src).select_with_index(*args)

@IQueryable.extend_linq(True)
def select_with_correspondence(src, selector, *args):
    return query(src).select_with_correspondence(selector, *args)

@IQueryable.extend_linq(True)
def select_many(src, *args):
    return query(src).select_many(*args)

@IQueryable.extend_linq(True)
def select_many_with_index(src, *args):
    return query(src).select_many_with_index(*args)

@IQueryable.extend_linq(True)
def select_many_with_correspondence(src, *args):
    return query(src).select_many_with_correspondence(*args)

@IQueryable.extend_linq(True)
def group_by(src, *args):
    return query(src).group_by(*args)

# filter

@IQueryable.extend_linq(True)
def where(src, predicate):
    return query(src).where(predicate)

@IQueryable.extend_linq(True)
def of_type(src, classinfo):
    return query(src).of_type(classinfo)

@IQueryable.extend_linq(True)
def take(src, *args):
    return query(src).take(*args)

@IQueryable.extend_linq(True)
def take_while(src, predicate):
    return query(src).take_while(predicate)

@IQueryable.extend_linq(True)
def skip(src, *args):
    return query(src).skip(*args)

@IQueryable.extend_linq(True)
def skip_while(src, predicate):
    return query(src).skip_while(predicate)

@IQueryable.extend_linq(True)
def distinct(src, *args):
    return query(src).distinct(*args)

# sort

@IQueryable.extend_linq(True)
def order_by(src, *args):
    return query(src).order_by(*args)

@IQueryable.extend_linq(True)
def order_by_descending(src, *args):
    return query(src).order_by_descending(*args)

@IQueryable.extend_linq(True)
def reverse(src):
    return query(src).reverse()

# get one elements

@IQueryable.extend_linq(False)
def default_if_empty(src, default):
    return query(src).default_if_empty(default)

@IQueryable.extend_linq(False)
def first(src, *args):
    return query(src).first(*args)

@IQueryable.extend_linq(False)
def first_or_default(src, default, *args):
    return query(src).first_or_default(default, *args)

@IQueryable.extend_linq(False)
def last(src, *args):
    return query(src).last(*args)

@IQueryable.extend_linq(False)
def last_or_default(src, default, *args):
    return query(src).last_or_default(default, *args)

@IQueryable.extend_linq(False)
def single(src, *args):
    return query(src).single(*args)

@IQueryable.extend_linq(False)
def single_or_default(src, default, *args):
    return query(src).single_or_default(default, *args)

@IQueryable.extend_linq(False)
def element_at(src, index):
    return query(src).element_at(index)

# get queryable props

@IQueryable.extend_linq(False)
def count(src, *args):
    return query(src).count(*args)

# two collection operations

@IQueryable.extend_linq(True)
def concat(src, other):
    return query(src).concat(other)

@IQueryable.extend_linq(True)
def difference(src, other, *args):
    return query(src).difference(other, *args)

@IQueryable.extend_linq(True)
def intersect(src, other, *args):
    return query(src).intersect(other, *args)

@IQueryable.extend_linq(True)
def union(src, other, *args):
    return query(src).union(other, *args)

@IQueryable.extend_linq(True)
def join(src, inner_iterable, *args):
    return query(src).join(inner_iterable, *args)

@IQueryable.extend_linq(True)
def group_join(src, inner_iterable, *args):
    return query(src).group_join(inner_iterable, *args)

@IQueryable.extend_linq(True)
def zip(src, other, *args):
    return query(src).zip(other, *args)

# for numbers

@IQueryable.extend_linq(False)
def min(src, *args):
    return query(src).min(*args)

@IQueryable.extend_linq(False)
def max(src, *args):
    return query(src).max(*args)

# aggregates

@IQueryable.extend_linq(False)
def sum(src, *args):
    return query(src).sum(*args)

@IQueryable.extend_linq(False)
def average(src, *args):
    return query(src).average(*args)

@IQueryable.extend_linq(False)
def aggregate(src, reducer, seed, result_selector):
    return query(src).aggregate(reducer, seed, result_selector)

# logic operations

@IQueryable.extend_linq(False)
def any(src, *args):
    return query(src).any(*args)

@IQueryable.extend_linq(False)
def all(src, *args):
    return query(src).all(*args)

@IQueryable.extend_linq(False)
def contains(src, value, *args):
    return query(src).contains(value, *args)

@IQueryable.extend_linq(False)
def sequence_equal(src, other, *args):
    return query(src).sequence_equal(other, *args)

# get iter result

@IQueryable.extend_linq(False)
def to_list(self) -> List[T]:
    return list(self)

@IQueryable.extend_linq(False)
def to_tuple(self) -> tuple:
    return tuple(self)

@IQueryable.extend_linq(False)
def to_set(self) -> Set[T]:
    return query(self).to_set()

@IQueryable.extend_linq(False)
def to_dict(self,
            key_selector: Callable[[T], TK] = identity,
            value_selector: Callable[[T], TV] = identity) -> Dict[TK, TV]:
    return query(self).to_dictionary(key_selector, value_selector)

@IQueryable.extend_linq(False)
def each(self, action: Callable[[T], None]) -> None:
    for item in self:
        action(item)

# for load outside:
_ = None
