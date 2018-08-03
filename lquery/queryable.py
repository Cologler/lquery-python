# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod, abstractproperty
from typing import Optional, Callable
from collections import namedtuple
import operator

from typeguard import typechecked
from asq import query as Q
from asq.selectors import identity
from asq.namedelements import IndexedElement, KeyedElement

from .expr import parameter, call
from .func import (
    # not in ASQ
    to_memory,
    # transforms
    select, select_with_index, select_with_correspondence,
    select_many, select_many_with_index, select_many_with_correspondence,
    group_by,
    # filter
    where, of_type, take, take_while, skip, skip_while, distinct,
    # sort
    order_by, order_by_descending, reverse,
    # get one elements
    default_if_empty, first, first_or_default, last, last_or_default,
    single, single_or_default, element_at,
    # get queryable props
    count,
    # two collection operations
    concat, difference, intersect, union, join, group_join, zip,
    # for numbers
    min, max,
    # aggregates
    sum, average,
    # logic operations
    any, all, contains, sequence_equal,
)

class IQueryable:
    '''
    interface of `Queryable`
    '''
    @abstractproperty
    def src(self):
        raise NotImplementedError


class Querys:
    def __init__(self, *exprs):
        self._exprs = exprs

    def __str__(self):
        return '.'.join(x.to_str(is_method=True) for x in self._exprs)

    def __add__(self, other):
        return Querys(*self._exprs, *other.exprs)

    @property
    def exprs(self):
        return self._exprs

    def then(self, call_expr):
        return Querys(*self._exprs, call_expr)


EMPTY_QUERYS = Querys()


ReduceInfoNode = namedtuple('ReduceInfoNode', ['type', 'expr'])


class ReduceInfo:
    TYPE_MEMORY     = 1
    TYPE_SQL        = 2
    TYPE_NOT_EXEC   = 3

    MODE_NORMAL     = 21
    # the query has conflict, so the result always are empty.
    MODE_EMPTY      = 22

    _PRINT_TABLE = {
        1: 'MEM',
        2: 'SQL',
        3: ''
    }

    def __init__(self, queryable: IQueryable):
        self.querable = queryable # need to set from stack top.
        self._details = []
        self._mode = self.MODE_NORMAL
        self._mode_reason = None

    def add_node(self, type_, expr):
        self._details.append(ReduceInfoNode(type_, expr))

    def set_mode(self, mode, reason: str):
        if mode not in (self.MODE_NORMAL, self.MODE_EMPTY):
            raise ValueError
        self._mode = mode
        self._mode_reason = reason

    @property
    def mode(self):
        return self._mode

    @property
    def details(self):
        return self._details[:]

    def print(self):
        if self._mode == self.MODE_NORMAL:
            if all(d.type == self.TYPE_MEMORY for d in self.details):
                reduce_info_str = '    all exec in memory'
            elif all(d.type == self.TYPE_SQL for d in self.details):
                reduce_info_str = '    all exec in SQL'
            else:
                lines = []
                for type_, expr in self.details:
                    lines.append(f'    [{self._PRINT_TABLE[type_]}] {expr.to_str(is_method=True)}')
                reduce_info_str = '\n'.join(lines)
        elif self._mode == self.MODE_EMPTY:
            reduce_info_str = f'    all query was skiped since always empty: {self._mode_reason}'
        else:
            raise NotImplementedError
        print(f'reduce info of:\n  {self.querable}\n=>\n{reduce_info_str}')


class IQueryProvider:
    '''
    interface of `QueryProvider`
    '''
    @abstractmethod
    def execute(self, queryable: IQueryable, call_expr):
        '''
        return a `IQueryable` or a value by `call_expr`.

        for example, if the `call_expr.func` is `count`, return value is a `int`
        '''
        raise NotImplementedError

    @abstractmethod
    def get_reduce_info(self, queryable: IQueryable) -> ReduceInfo:
        '''
        get reduce info in console.
        '''
        raise NotImplementedError


class Queryable(IQueryable):
    @typechecked
    def __init__(self, src: Optional[IQueryable], provider: IQueryProvider, querys: Querys):
        self._src = src
        self._provider = provider
        self._querys = querys

    @property
    def src(self):
        '''`src` can be `None` if the Queryable is root.'''
        return self._src

    @property
    def querys(self):
        return self._querys

    @property
    def expr(self):
        if self._querys.exprs:
            return self._querys.exprs[-1]
        return None

    def __str__(self):
        src = self
        while src.src:
            src = src.src
        src_str = str(src)
        lines = [src_str]
        for expr in self._querys.exprs:
            lines.append(expr.to_str(is_method=True))
        return '\n    .'.join(lines)

    def __iter__(self):
        raise NotImplementedError('you should implement the query in subclass.')

    def _then_query(self, call_expr):
        return self._provider.execute(self, call_expr)

    def get_reduce_info(self):
        '''
        print reduce info in console.
        '''
        return self._provider.get_reduce_info(self)

    # not in ASQ

    def to_memory(self):
        '''
        force iter in memory.
        '''
        call_expr = call(to_memory, parameter('self'))
        return self._then_query(call_expr)

    # transforms

    @typechecked
    def select(self, selector: Callable):
        call_expr = call(select, parameter('self'), selector)
        return self._then_query(call_expr)

    @typechecked
    def select_with_index(self, selector: Callable=IndexedElement, transform: Callable=identity):
        call_expr = call(select_with_index, parameter('self'), selector, transform)
        return self._then_query(call_expr)

    @typechecked
    def select_with_correspondence(self, selector: Callable, result_selector: Callable=KeyedElement):
        call_expr = call(select_with_correspondence, parameter('self'), selector, result_selector)
        return self._then_query(call_expr)

    @typechecked
    def select_many(self, collection_selector: Callable=identity, result_selector: Callable=identity):
        call_expr = call(select_many, parameter('self'), collection_selector, result_selector)
        return self._then_query(call_expr)

    @typechecked
    def select_many_with_index(self, collection_selector: Callable=IndexedElement,
            result_selector: Callable=lambda source_element, collection_element: collection_element):
        call_expr = call(select_many_with_index, parameter('self'),
            collection_selector, result_selector)
        return self._then_query(call_expr)

    @typechecked
    def select_many_with_correspondence(self,
            collection_selector: Callable=identity, result_selector: Callable=KeyedElement):
        call_expr = call(select_many_with_correspondence, parameter('self'),
            collection_selector, result_selector)
        return self._then_query(call_expr)

    @typechecked
    def group_by(self, key_selector: Callable=identity,
            element_selector: Callable=identity, result_selector: Callable=lambda key, grouping: grouping):
        call_expr = call(group_by, parameter('self'), key_selector, element_selector, result_selector)
        return self._then_query(call_expr)

    # filter

    @typechecked
    def where(self, predicate: Callable):
        '''
        Filters elements according to whether they match a predicate.
        '''
        call_expr = call(where, parameter('self'), predicate)
        return self._then_query(call_expr)

    @typechecked
    def of_type(self, type_: type):
        '''
        Filters elements according to whether they are of a certain type.
        '''
        call_expr = call(of_type, parameter('self'), type_)
        return self._then_query(call_expr)

    @typechecked
    def take(self, count_: int):
        call_expr = call(take, parameter('self'), count_)
        return self._then_query(call_expr)

    @typechecked
    def take_while(self, predicate: Callable):
        call_expr = call(take_while, parameter('self'), predicate)
        return self._then_query(call_expr)

    @typechecked
    def skip(self, count_: int):
        call_expr = call(skip, parameter('self'), count_)
        return self._then_query(call_expr)

    @typechecked
    def skip_while(self, predicate: Callable):
        call_expr = call(skip_while, parameter('self'), predicate)
        return self._then_query(call_expr)

    @typechecked
    def distinct(self, selector: Callable=identity):
        call_expr = call(distinct, parameter('self'), selector)
        return self._then_query(call_expr)

    # sort

    @typechecked
    def order_by(self, key_selector: Callable=identity):
        call_expr = call(order_by, parameter('self'), key_selector)
        return self._then_query(call_expr)

    @typechecked
    def order_by_descending(self, key_selector: Callable=identity):
        call_expr = call(order_by_descending, parameter('self'), key_selector)
        return self._then_query(call_expr)

    def reverse(self):
        call_expr = call(reverse, parameter('self'))
        return self._then_query(call_expr)

    # get one element

    def default_if_empty(self, default):
        call_expr = call(default_if_empty, parameter('self'), default)
        return self._then_query(call_expr)

    def first(self, predicate=None):
        call_expr = call(first, parameter('self'), predicate)
        return self._then_query(call_expr)

    def first_or_default(self, default, predicate=None):
        call_expr = call(first_or_default, parameter('self'), default, predicate)
        return self._then_query(call_expr)

    def last(self, predicate=None):
        call_expr = call(last, parameter('self'), predicate)
        return self._then_query(call_expr)

    def last_or_default(self, default, predicate=None):
        call_expr = call(last_or_default, parameter('self'), default, predicate)
        return self._then_query(call_expr)

    def single(self, predicate=None):
        call_expr = call(single, parameter('self'), predicate)
        return self._then_query(call_expr)

    def single_or_default(self, default, predicate=None):
        call_expr = call(single_or_default, parameter('self'), default, predicate)
        return self._then_query(call_expr)

    def element_at(self, index):
        call_expr = call(element_at, parameter('self'), index)
        return self._then_query(call_expr)

    # get queryable props

    def count(self, predicate=None) -> int:
        call_expr = call(count, parameter('self'), predicate)
        return self._then_query(call_expr)

    # two collection operations

    def concat(self, second_iterable):
        call_expr = call(concat, parameter('self'), second_iterable)
        return self._then_query(call_expr)

    def difference(self, second_iterable, selector=identity):
        call_expr = call(difference, parameter('self'), second_iterable, selector)
        return self._then_query(call_expr)

    def intersect(self, second_iterable, selector=identity):
        call_expr = call(intersect, parameter('self'), second_iterable, selector)
        return self._then_query(call_expr)

    def union(self, second_iterable, selector=identity):
        call_expr = call(union, parameter('self'), second_iterable, selector)
        return self._then_query(call_expr)

    def join(self, inner_iterable, outer_key_selector=identity,
             inner_key_selector=identity,
             result_selector=lambda outer, inner: (outer, inner)):
        call_expr = call(join, parameter('self'),
            inner_iterable, outer_key_selector, inner_key_selector, result_selector)
        return self._then_query(call_expr)

    def group_join(self, inner_iterable, outer_key_selector=identity, inner_key_selector=identity,
                   result_selector=lambda outer, grouping: grouping):
        call_expr = call(group_join, parameter('self'),
            inner_iterable, outer_key_selector, inner_key_selector, result_selector)
        return self._then_query(call_expr)

    def zip(self, second_iterable, result_selector=lambda x, y: (x, y)):
        call_expr = call(zip, parameter('self'), second_iterable, result_selector)
        return self._then_query(call_expr)

    # for numbers

    @typechecked
    def min(self, selector: Callable=identity):
        call_expr = call(min, parameter('self'), selector)
        return self._then_query(call_expr)

    @typechecked
    def max(self, selector: Callable=identity):
        call_expr = call(max, parameter('self'), selector)
        return self._then_query(call_expr)

    # aggregates

    @typechecked
    def sum(self, selector: Callable=identity):
        call_expr = call(sum, parameter('self'), selector)
        return self._then_query(call_expr)

    @typechecked
    def average(self, selector: Callable=identity):
        call_expr = call(average, parameter('self'), selector)
        return self._then_query(call_expr)

    @typechecked
    def aggregate(self, reducer: Callable, seed, result_selector: Callable=identity):
        call_expr = call(aggregate, parameter('self'), reducer, seed, result_selector)
        return self._then_query(call_expr)

    # logic operations

    @typechecked
    def any(self, predicate: Callable=None):
        call_expr = call(any, parameter('self'), predicate)
        return self._then_query(call_expr)

    @typechecked
    def all(self, predicate: Callable=bool):
        call_expr = call(all, parameter('self'), predicate)
        return self._then_query(call_expr)

    @typechecked
    def contains(self, value, equality_comparer: Callable=operator.eq):
        call_expr = call(contains, parameter('self'), value, equality_comparer)
        return self._then_query(call_expr)

    @typechecked
    def sequence_equal(self, other, equality_comparer: Callable=operator.eq) -> bool:
        call_expr = call(sequence_equal, parameter('self'), other, equality_comparer)
        return self._then_query(call_expr)

    # get iter result

    def to_list(self) -> list:
        return list(self)

    def to_tuple(self) -> tuple:
        return tuple(self)

    def to_set(self) -> set:
        return Q(self).to_set()

    def to_dict(self, key_selector=identity, value_selector=identity) -> dict:
        return Q(self).to_dictionary(key_selector, value_selector)


class QueryProvider(IQueryProvider):

    def get_reduce_info(self, queryable: IQueryable) -> ReduceInfo:
        '''
        get reduce info in console.
        '''
        if queryable.src:
            info: ReduceInfo = queryable.src.get_reduce_info()
            info.querable = queryable
        else:
            info = ReduceInfo(queryable)
        return info

    def execute(self, queryable: IQueryable, call_expr):
        from .iterable import PROVIDER as ITERABLE_PROVIDER
        return ITERABLE_PROVIDER.execute(queryable, call_expr)
