# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# define some common extension functions for convert to SQL.
# ----------

from typing import Callable, Set, Dict, List, TypeVar
import operator

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
def select_with_index(src, selector=IndexedElement, transform=identity):
    return query(src).select_with_index(selector, transform)

@IQueryable.extend_linq(True)
def select_with_correspondence(src, selector, result_selector=KeyedElement):
    return query(src).select_with_correspondence(selector, result_selector)

@IQueryable.extend_linq(True)
def select_many(src, collection_selector=identity, result_selector=identity):
    return query(src).select_many(collection_selector, result_selector)

@IQueryable.extend_linq(True)
def select_many_with_index(src,
        collection_selector=IndexedElement,
        result_selector=lambda source_element, collection_element: collection_element):
    return query(src).select_many_with_index(collection_selector, result_selector)

@IQueryable.extend_linq(True)
def select_many_with_correspondence(src,
        collection_selector=identity,
        result_selector=KeyedElement):
    return query(src).select_many_with_correspondence(collection_selector, result_selector)

@IQueryable.extend_linq(True)
def group_by(src, key_selector=identity, element_selector=identity,
             result_selector=lambda key, grouping: grouping):
    return query(src).group_by(key_selector, element_selector, result_selector)

# filter

@IQueryable.extend_linq(True)
def where(src, predicate):
    return query(src).where(predicate)

@IQueryable.extend_linq(True)
def of_type(src, classinfo):
    return query(src).of_type(classinfo)

@IQueryable.extend_linq(True)
def take(src, count_=1):
    return query(src).take(count_)

@IQueryable.extend_linq(True)
def take_while(src, predicate):
    return query(src).take_while(predicate)

@IQueryable.extend_linq(True)
def skip(src, count_=1):
    return query(src).skip(count_)

@IQueryable.extend_linq(True)
def skip_while(src, predicate):
    return query(src).skip_while(predicate)

@IQueryable.extend_linq(True)
def distinct(src, selector=identity):
    return query(src).distinct(selector)

# sort

@IQueryable.extend_linq(True)
def order_by(src, key_selector=identity):
    return query(src).order_by(key_selector)

@IQueryable.extend_linq(True)
def order_by_descending(src, key_selector=identity):
    return query(src).order_by_descending(key_selector)

@IQueryable.extend_linq(True)
def reverse(src):
    return query(src).reverse()

# get one elements

@IQueryable.extend_linq(False)
def default_if_empty(src, default):
    return query(src).default_if_empty(default)

@IQueryable.extend_linq(False)
def first(src, predicate=None):
    return query(src).first(predicate)

@IQueryable.extend_linq(False)
def first_or_default(src, default, predicate=None):
    return query(src).first_or_default(default, predicate)

@IQueryable.extend_linq(False)
def last(src, predicate=None):
    return query(src).last(predicate)

@IQueryable.extend_linq(False)
def last_or_default(src, default, predicate=None):
    return query(src).last_or_default(default, predicate)

@IQueryable.extend_linq(False)
def single(src, predicate=None):
    return query(src).single(predicate)

@IQueryable.extend_linq(False)
def single_or_default(src, default, predicate=None):
    return query(src).single_or_default(default, predicate)

@IQueryable.extend_linq(False)
def element_at(src, index):
    return query(src).element_at(index)

# get queryable props

@IQueryable.extend_linq(False)
def count(src, predicate=None):
    return query(src).count(predicate)

# two collection operations

@IQueryable.extend_linq(True)
def concat(src, other):
    return query(src).concat(other)

@IQueryable.extend_linq(True)
def difference(src, other, selector=identity):
    return query(src).difference(other, selector)

@IQueryable.extend_linq(True)
def intersect(src, other, selector=identity):
    return query(src).intersect(other, selector)

@IQueryable.extend_linq(True)
def union(src, other, selector=identity):
    return query(src).union(other, selector)

@IQueryable.extend_linq(True)
def join(src, inner_iterable,
         outer_key_selector=identity,
         inner_key_selector=identity,
         result_selector=lambda outer, inner: (outer, inner)):
    return query(src).join(inner_iterable, outer_key_selector, inner_key_selector, result_selector)

@IQueryable.extend_linq(True)
def group_join(src,
               inner_iterable,
               outer_key_selector=identity,
               inner_key_selector=identity,
               result_selector=lambda outer, grouping: grouping):
    return query(src).group_join(inner_iterable, outer_key_selector, inner_key_selector, result_selector)

@IQueryable.extend_linq(True)
def zip(src, other, result_selector=lambda x, y: (x, y)):
    return query(src).zip(other, result_selector)

# for numbers

@IQueryable.extend_linq(False)
def min(src, selector=identity):
    return query(src).min(selector)

@IQueryable.extend_linq(False)
def max(src, selector=identity):
    return query(src).max(selector)

# aggregates

@IQueryable.extend_linq(False)
def sum(src, selector=identity):
    return query(src).sum(selector)

@IQueryable.extend_linq(False)
def average(src, selector=identity):
    return query(src).average(selector)

@IQueryable.extend_linq(False)
def aggregate(src, reducer, seed, result_selector=identity):
    return query(src).aggregate(reducer, seed, result_selector)

# logic operations

@IQueryable.extend_linq(False)
def any(src, predicate=None):
    return query(src).any(predicate)

@IQueryable.extend_linq(False)
def all(src, predicate=bool):
    return query(src).all(predicate)

@IQueryable.extend_linq(False)
def contains(src, value, comparer=operator.eq):
    return query(src).contains(value, comparer)

@IQueryable.extend_linq(False)
def sequence_equal(src, other, comparer=operator.eq):
    return query(src).sequence_equal(other, comparer)

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
def for_each(self, action: Callable[[T], None]) -> None:
    for item in self:
        action(item)

# for load outside:
_ = None
