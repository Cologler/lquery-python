# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from typing import Optional, Callable
from collections import namedtuple

from typeguard import typechecked
from asq import query as Q
from asq.selectors import identity

from .expr import parameter, call, CallExpr
from .query import Query, EMPTY
from .func import where, select, select_many, take, skip, to_memory

class IQueryable:
    '''
    interface of `Queryable`
    '''
    pass


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
        self._querable = queryable
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
        print(f'reduce info of:\n  {self._querable}\n=>\n{reduce_info_str}')


class IQueryProvider:
    '''
    interface of `QueryProvider`
    '''
    @abstractmethod
    def execute(self, queryable: IQueryable):
        raise NotImplementedError

    def get_reduce_info(self, queryable: IQueryable) -> ReduceInfo:
        '''
        get reduce info in console.
        '''
        return ReduceInfo(queryable)

    @abstractmethod
    def then_query(self, queryable: IQueryable, query_expr) -> IQueryable:
        raise NotImplementedError


class Queryable(IQueryable):
    @typechecked
    def __init__(self, src: Optional[IQueryable], provider: IQueryProvider, query: Query = EMPTY, *, expr: CallExpr=None):
        self._src = src
        self._provider = provider
        self._query = query
        self._expr = expr

    @property
    def src(self):
        '''`src` can be `None` if the Queryable is root.'''
        return self._src

    @property
    def query(self):
        '''get the assigned `Query`.'''
        return self._query

    @property
    def expr(self):
        return self._expr

    def __str__(self):
        src_str = 'Queryable(?)' if self._src is None else str(self._src)
        lines = [src_str]
        for expr in self._query.exprs:
            lines.append(expr.to_str(is_method=True))
        return '\n    .'.join(lines)

    def __iter__(self):
        yield from self._provider.execute(self)

    def to_list(self):
        return list(self)

    def to_dict(self, key_selector=identity, value_selector=identity):
        return Q(self).to_dictionary(key_selector, value_selector)

    def _then_query(self, call_expr):
        return self._provider.then_query(self, call_expr)

    @typechecked
    def where(self, predicate: Callable):
        call_expr = call(where, parameter('self'), predicate)
        return self._then_query(call_expr)

    @typechecked
    def select(self, selector: Callable):
        call_expr = call(select, parameter('self'), selector)
        return self._then_query(call_expr)

    @typechecked
    def select_many(self, collection_selector: Callable=identity, result_selector: Callable=identity):
        call_expr = call(select_many, parameter('self'), collection_selector, result_selector)
        return self._then_query(call_expr)

    @typechecked
    def take(self, count: int):
        call_expr = call(take, parameter('self'), count)
        return self._then_query(call_expr)

    @typechecked
    def skip(self, count: int):
        call_expr = call(skip, parameter('self'), count)
        return self._then_query(call_expr)

    def to_memory(self):
        '''
        force iter in memory.
        '''
        call_expr = call(to_memory, parameter('self'))
        return self._then_query(call_expr)

    def get_reduce_info(self):
        '''
        print reduce info in console.
        '''
        return self._provider.get_reduce_info(self)


class QueryProvider(IQueryProvider):

    def then_query(self, queryable: Queryable, query_expr):
        query = queryable.query.then(query_expr)
        src = queryable.src or queryable
        return Queryable(src, self, query, expr=query_expr)
