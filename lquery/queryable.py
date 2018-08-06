# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod, abstractproperty
from typing import Optional, Union, List
from collections import namedtuple
from collections.abc import Iterable
import operator

from typeguard import typechecked
from asq import query as Q
from asq.selectors import identity
from asq.namedelements import IndexedElement, KeyedElement

from .expr import Make, CallExpr, ValueExpr
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
    sum, average, aggregate,
    # logic operations
    any, all, contains, sequence_equal,
)

class IQueryable:
    '''
    interface of `Queryable`
    '''
    @abstractproperty
    def expr(self) -> Union[ValueExpr, CallExpr]:
        raise NotImplementedError

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError('you should implement the query in subclass.')


ReduceInfoNode = namedtuple('ReduceInfoNode', ['type', 'expr'])


class ReduceInfo:
    # pylint: disable=C0326
    TYPE_SRC        = 0
    TYPE_MEMORY     = 1
    TYPE_SQL        = 2
    TYPE_NOT_EXEC   = 3

    MODE_NORMAL     = 21
    # the query has conflict, so the result always are empty.
    MODE_EMPTY      = 22
    # pylint: enable=C0326

    _PRINT_TABLE = {
        0: 'SRC',
        1: 'MEM',
        2: 'SQL',
        3: ''
    }

    def __init__(self, queryable: IQueryable):
        self.querable = queryable # need to set from stack top.
        self._details: List[ReduceInfoNode] = []

    def add_node(self, type_, expr):
        self._details.append(ReduceInfoNode(type_, expr))

    @property
    def mode(self):
        return self.MODE_NORMAL

    @property
    def details(self):
        return self._details[:]

    def get_desc_strs(self):
        strs = []
        if all(d.type == self.TYPE_MEMORY for d in self.details):
            strs = ['all exec in memory']
        elif all(d.type == self.TYPE_SQL for d in self.details):
            strs = ['all exec in SQL']
        else:
            strs = []
            for type_, expr in self.details:
                expr_str = None
                if isinstance(expr, CallExpr):
                    expr_str = expr.to_str(is_method=True)
                else:
                    expr_str = str(expr.value)
                strs.append(f'[{self._PRINT_TABLE[type_]}] {expr_str}')
        return strs

    def print(self):
        desc_strs = self.get_desc_strs()
        reduce_info_str = '\n'.join('    ' + line for line in desc_strs)
        print(f'reduce info of:\n  {self.querable}\n=>\n{reduce_info_str}')


class IQueryProvider:

    '''
    interface of `QueryProvider`
    '''
    @abstractmethod
    def execute(self, expr: Union[ValueExpr, CallExpr]):
        '''
        return a `IQueryable` or a value by `expr`.

        for example, if the `expr.func.resolve_value()` is `count`, return value should be a number.
        '''
        raise NotImplementedError


class Queryable(IQueryable):
    @typechecked
    def __init__(self, expr: Union[ValueExpr, CallExpr], provider: IQueryProvider):
        self._expr = expr
        self._provider = provider

    @property
    def querys(self):
        raise NotImplementedError
        return self._querys

    @property
    def expr(self):
        return self._expr

    def __str__(self):
        expr = self.expr
        exprs = [expr]
        while isinstance(expr, CallExpr):
            expr = expr.args[0].value.expr
            exprs.append(expr)
        exprs.reverse()
        lines = [f'Queryable({repr(exprs[0].value)})']
        for expr in exprs[1:]:
            lines.append(expr.to_str(is_method=True))
        return '\n    .'.join(lines)

    def _then_query(self, call_expr):
        return self._provider.execute(self, call_expr)

    def _then(self, func, *args):
        allargs = [func, self, *args]
        next_expr = Make.call(*[Make.ref(a) for a in allargs])
        return self._provider.execute(next_expr)

    def get_reduce_info(self):
        '''
        print reduce info in console.
        '''
        reduce_info = ReduceInfo(self)
        for queryable in get_queryables(self.expr):
            queryable.update_reduce_info(reduce_info)
        self.update_reduce_info(reduce_info)
        return reduce_info

    def update_reduce_info(self, reduce_info: ReduceInfo):
        pass

    # not in ASQ

    def to_memory(self):
        '''
        force iter in memory.
        '''
        return self._then(to_memory)

    # transforms

    @typechecked
    def select(self, selector: callable):
        return self._then(select, selector)

    @typechecked
    def select_with_index(self, selector: callable=IndexedElement, transform: callable=identity):
        return self._then(select_with_index, selector, transform)

    @typechecked
    def select_with_correspondence(self, selector: callable,
                                   result_selector: callable=KeyedElement):
        return self._then(select_with_correspondence, selector, result_selector)

    @typechecked
    def select_many(self, collection_selector: callable=identity,
                    result_selector: callable=identity):
        return self._then(select_many, collection_selector, result_selector)

    @typechecked
    def select_many_with_index(self, collection_selector: callable = IndexedElement,
            result_selector: callable = lambda source_element, collection_element: collection_element):
        return self._then(select_many_with_index, collection_selector, result_selector)

    @typechecked
    def select_many_with_correspondence(self,
            collection_selector: callable=identity, result_selector: callable=KeyedElement):
        return self._then(select_many_with_correspondence, collection_selector, result_selector)

    @typechecked
    def group_by(self, key_selector: callable=identity, element_selector: callable=identity,
            result_selector: callable=lambda key, grouping: grouping):
        return self._then(group_by, key_selector, element_selector, result_selector)

    # filter

    @typechecked
    def where(self, predicate: callable):
        '''
        Filters elements according to whether they match a predicate.
        '''
        return self._then(where, predicate)

    @typechecked
    def of_type(self, type_: type):
        '''
        Filters elements according to whether they are of a certain type.
        '''
        return self._then(of_type, type_)

    @typechecked
    def take(self, count_: int):
        return self._then(take, count_)

    @typechecked
    def take_while(self, predicate: callable):
        return self._then(take_while, predicate)

    @typechecked
    def skip(self, count_: int):
        return self._then(skip, count_)

    @typechecked
    def skip_while(self, predicate: callable):
        return self._then(skip_while, predicate)

    @typechecked
    def distinct(self, selector: callable=identity):
        return self._then(distinct, selector)

    # sort

    @typechecked
    def order_by(self, key_selector: callable=identity):
        return self._then(order_by, key_selector)

    @typechecked
    def order_by_descending(self, key_selector: callable=identity):
        return self._then(order_by_descending, key_selector)

    def reverse(self):
        return self._then(reverse)

    # get one element

    def default_if_empty(self, default):
        return self._then(default_if_empty, default)

    @typechecked
    def first(self, predicate: Optional[callable]=None):
        return self._then(first, predicate)

    @typechecked
    def first_or_default(self, default, predicate: Optional[callable]=None):
        return self._then(first_or_default, default, predicate)

    @typechecked
    def last(self, predicate: Optional[callable]=None):
        return self._then(last, predicate)

    @typechecked
    def last_or_default(self, default, predicate: Optional[callable]=None):
        return self._then(last_or_default, default, predicate)

    @typechecked
    def single(self, predicate: Optional[callable]=None):
        return self._then(single, predicate)

    @typechecked
    def single_or_default(self, default, predicate: Optional[callable]=None):
        return self._then(single_or_default, default, predicate)

    @typechecked
    def element_at(self, index: int):
        return self._then(element_at, index)

    # get queryable props

    @typechecked
    def count(self, predicate: Optional[callable]=None) -> int:
        return self._then(count, predicate)

    # two collection operations

    @typechecked
    def concat(self, other: Iterable):
        return self._then(concat, other)

    @typechecked
    def difference(self, other: Iterable, selector=identity):
        return self._then(difference, other, selector)

    @typechecked
    def intersect(self, other: Iterable, selector=identity):
        return self._then(intersect, other, selector)

    @typechecked
    def union(self, other: Iterable, selector=identity):
        return self._then(union, other, selector)

    @typechecked
    def join(self, inner_iterable: Iterable,
             outer_key_selector: callable=identity, inner_key_selector: callable=identity,
             result_selector: callable=lambda outer, inner: (outer, inner)):
        return self._then(join, inner_iterable,
                          outer_key_selector, inner_key_selector, result_selector)

    @typechecked
    def group_join(self, inner_iterable: Iterable,
                   outer_key_selector: callable=identity, inner_key_selector: callable=identity,
                   result_selector: callable=lambda outer, grouping: grouping):
        return self._then(group_join, inner_iterable,
                          outer_key_selector, inner_key_selector, result_selector)

    @typechecked
    def zip(self, other: Iterable, result_selector: callable=lambda x, y: (x, y)):
        return self._then(zip, other, result_selector)

    # for numbers

    @typechecked
    def min(self, selector: callable=identity):
        return self._then(min, selector)

    @typechecked
    def max(self, selector: callable=identity):
        return self._then(max, selector)

    # aggregates

    @typechecked
    def sum(self, selector: callable=identity):
        return self._then(sum, selector)

    @typechecked
    def average(self, selector: callable=identity):
        return self._then(average, selector)

    @typechecked
    def aggregate(self, reducer: callable, seed, result_selector: callable=identity):
        return self._then(aggregate, reducer, seed, result_selector)

    # logic operations

    @typechecked
    def any(self, predicate: callable=None):
        return self._then(any, predicate)

    @typechecked
    def all(self, predicate: callable=bool):
        return self._then(all, predicate)

    @typechecked
    def contains(self, value, equality_comparer: callable=operator.eq):
        return self._then(contains, value, equality_comparer)

    @typechecked
    def sequence_equal(self, other, equality_comparer: callable=operator.eq) -> bool:
        return self._then(sequence_equal, other, equality_comparer)

    # get iter result

    def to_list(self) -> list:
        return list(self)

    def to_tuple(self) -> tuple:
        return tuple(self)

    def to_set(self) -> set:
        return Q(self).to_set()

    def to_dict(self, key_selector=identity, value_selector=identity) -> dict:
        return Q(self).to_dictionary(key_selector, value_selector)


def get_queryables(expr):
    '''
    get queryables chain as a `tuple`.
    '''
    queryables = []
    while isinstance(expr, CallExpr):
        queryables.append(expr.args[0].value)
        expr = queryables[-1].expr
    # the first (<ValueExpr>expr).value is src, which should not be the queryable.
    queryables.reverse()
    return tuple(queryables)

def get_prev_queryable(expr):
    '''
    get previous queryable.
    '''
    if isinstance(expr, CallExpr):
        return expr.args[0].value
    return expr.value

def get_exprs(expr):
    exprs = []
    while isinstance(expr, CallExpr):
        exprs.append(expr)
        expr = exprs[-1].args[0].value.expr
    exprs.append(expr)
    return tuple(reversed(exprs))
