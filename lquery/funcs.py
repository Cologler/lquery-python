# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# define some common extension functions for convert to SQL.
# ----------

import abc
import itertools
from typing import Callable, Dict, List, TypeVar, Any
import operator

from asq import query
from asq.queryables import OutOfRangeError
from asq.selectors import identity
from asq.namedelements import IndexedElement, KeyedElement

from .queryable import IQueryable
from .enumerable import IEnumerable

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

def extend_linq(return_queryable: bool, name: str = None):
    def _(func):
        IQueryable.extend_linq(return_queryable, name)(func)
        IEnumerable.extend_linq(return_queryable, name)(func)
        return func
    return _

class LinqQuery:
    '''
    class `LinqQuery` is for type hint.

    for example, you may want to write:

    ```
    query: LinqQuery = enumerable([1, 2, 3]).where(lambda x: x > 1)
    query.? # should show auto-completion list here
    ```
    '''

    @abc.abstractmethod
    def __iter__(self):
        # added this method so linter will not show error.
        raise NotImplementedError

    # transforms

    @extend_linq(True)
    def select(self, selector) -> Any:
        return query(self).select(selector)

    #@extend_linq(True)
    #def select_with_index(self, selector=IndexedElement, transform=identity) -> Any:
    #    return query(self).select_with_index(selector, transform)

    #@extend_linq(True)
    #def select_with_correspondence(self, selector, result_selector=KeyedElement) -> Any:
    #    return query(self).select_with_correspondence(selector, result_selector)

    @extend_linq(True)
    def select_many(self, collection_selector=identity, result_selector=identity) -> Any:
        return query(self).select_many(collection_selector, result_selector)

    #@extend_linq(True)
    #def select_many_with_index(self,
    #        collection_selector=IndexedElement,
    #        result_selector=lambda source_element, collection_element: collection_element) -> Any:
    #    return query(self).select_many_with_index(collection_selector, result_selector)

    #@extend_linq(True)
    #def select_many_with_correspondence(self,
    #        collection_selector=identity,
    #        result_selector=KeyedElement) -> Any:
    #    return query(self).select_many_with_correspondence(collection_selector, result_selector)

    @extend_linq(True)
    def group_by(self, key_selector=identity, element_selector=identity,
                result_selector=lambda key, grouping: grouping) -> Any:
        return query(self).group_by(key_selector, element_selector, result_selector)

    # filter

    @extend_linq(True)
    def where(self, predicate) -> Any:
        return query(self).where(predicate)

    @extend_linq(True)
    def of_type(self, type_: type) -> Any:
        return query(self).of_type(type_)

    @extend_linq(True)
    def take(self, count_: int = 1) -> Any:
        return query(self).take(count_)

    @extend_linq(True)
    def take_while(self, predicate) -> Any:
        return query(self).take_while(predicate)

    @extend_linq(True)
    def skip(self, count_: int = 1) -> Any:
        return query(self).skip(count_)

    @extend_linq(True)
    def skip_while(self, predicate) -> Any:
        return query(self).skip_while(predicate)

    @extend_linq(True)
    def distinct(self, selector=identity) -> Any:
        return query(self).distinct(selector)

    # sort

    @extend_linq(True)
    def order_by(self, key_selector=identity) -> Any:
        return query(self).order_by(key_selector)

    @extend_linq(True)
    def order_by_descending(self, key_selector=identity) -> Any:
        return query(self).order_by_descending(key_selector)

    @extend_linq(True)
    def reverse(self) -> Any:
        return query(self).reverse()

    # get one elements

    @extend_linq(False)
    def first(self, predicate=None) -> Any:
        return query(self).first(predicate)

    @extend_linq(False)
    def first_or_default(self, default, predicate=None) -> Any:
        return query(self).first_or_default(default, predicate)

    @extend_linq(False)
    def last(self, predicate=None) -> Any:
        return query(self).last(predicate)

    @extend_linq(False)
    def last_or_default(self, default, predicate=None) -> Any:
        return query(self).last_or_default(default, predicate)

    @extend_linq(False)
    def single(self, predicate=None):
        return query(self).single(predicate)

    @extend_linq(False)
    def single_or_default(self, default, predicate=None):
        return query(self).single_or_default(default, predicate)

    @extend_linq(False)
    def element_at(self, index: int):
        source = query(self)
        if index < 0:
            source = source.reverse()
            index = -index
            index -= 1
        try:
            return source.element_at(index)
        except OutOfRangeError:
            raise IndexError

    # get queryable props

    @extend_linq(False)
    def count(self, predicate=None):
        return query(self).count(predicate)

    # two collection operations

    @extend_linq(True)
    def concat(self, other):
        return query(self).concat(other)

    @extend_linq(True)
    def difference(self, other, selector=identity):
        return query(self).difference(other, selector)

    @extend_linq(True)
    def intersect(self, other, selector=identity):
        return query(self).intersect(other, selector)

    @extend_linq(True)
    def union(self, other, selector=identity):
        return query(self).union(other, selector)

    @extend_linq(True)
    def join(self, inner_iterable,
            outer_key_selector=identity,
            inner_key_selector=identity,
            result_selector=lambda outer, inner: (outer, inner)):
        return query(self).join(inner_iterable, outer_key_selector, inner_key_selector, result_selector)

    @extend_linq(True)
    def group_join(self,
                inner_iterable,
                outer_key_selector=identity,
                inner_key_selector=identity,
                result_selector=lambda outer, grouping: grouping):
        return query(self).group_join(inner_iterable, outer_key_selector, inner_key_selector, result_selector)

    @extend_linq(True)
    def zip(self, second, *others):
        return zip(self, second, *others)

    @extend_linq(True)
    def zip_longest(self, second, *others, fill_value=None):
        return itertools.zip_longest(self, second, *others, fillvalue=fill_value)

    # for numbers

    @extend_linq(False)
    def min(self, selector=identity):
        return query(self).min(selector)

    @extend_linq(False)
    def max(self, selector=identity):
        return query(self).max(selector)

    # aggregates

    @extend_linq(False)
    def sum(self, selector=identity):
        return query(self).sum(selector)

    @extend_linq(False)
    def average(self, selector=identity):
        return query(self).average(selector)

    @extend_linq(False)
    def aggregate(self, reducer, seed, result_selector=identity):
        return query(self).aggregate(reducer, seed, result_selector)

    # logic operations

    @extend_linq(False)
    def any(self, predicate=None) -> bool:
        return query(self).any(predicate)

    @extend_linq(False)
    def all(self, predicate=bool) -> bool:
        return query(self).all(predicate)

    @extend_linq(False)
    def contains(self, value, comparer=operator.eq) -> bool:
        return query(self).contains(value, comparer)

    @extend_linq(False)
    def sequence_equal(self, other, comparer=operator.eq) -> bool:
        return query(self).sequence_equal(other, comparer)

    # get iter result

    @extend_linq(False)
    def to_list(self) -> List[T]:
        return list(self)

    @extend_linq(False)
    def to_dict(self,
                key_selector: Callable[[T], TK] = identity,
                value_selector: Callable[[T], TV] = identity) -> Dict[TK, TV]:
        return query(self).to_dictionary(key_selector, value_selector)

    @extend_linq(False)
    def for_each(self, action: Callable[[T], None]) -> None:
        for item in self:
            action(item)

# for load from outside:
_ = None
