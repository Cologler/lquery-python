# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from typing import Optional
from collections import namedtuple

from typeguard import typechecked
from asq import query as Q
from asq.selectors import identity

from .query import Query, EMPTY

class IQueryable:
    '''
    interface of `Queryable`
    '''
    pass


ReduceInfoNode = namedtuple('ReduceInfoNode', ['type', 'expr'])


class ReduceInfo:
    TYPE_MEMORY = 'MEM'
    TYPE_SQL = 'SQL'

    def __init__(self, queryable: IQueryable):
        self._querable = queryable
        self._details = []

    def add_node(self, type, expr):
        self._details.append(ReduceInfoNode(type, expr))

    @property
    def details(self):
        return self._details

    def print(self):
        if all(d.type == ReduceInfo.TYPE_MEMORY for d in self.details):
            reduce_info_str = 'all stmt exec in memory'
        elif all(d.type == ReduceInfo.TYPE_SQL for d in self.details):
            reduce_info_str = 'all stmt exec in SQL'
        else:
            lines = []
            for type_, expr in self.details:
                lines.append(f'    [{type_}] {expr.to_str(is_method=True)}')
            reduce_info_str = '\n'.join(lines)
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


class Queryable(IQueryable):
    @typechecked
    def __init__(self, src: Optional[IQueryable], provider: IQueryProvider, query: Query = EMPTY):
        self._src = src
        self._provider = provider
        self._query = query

    @property
    def src(self):
        '''`src` can be `None` if the Queryable is root.'''
        return self._src

    @property
    def query(self):
        '''get the assigned `Query`.'''
        return self._query

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

    def update_query(self, query):
        '''
        return a new queryable with the query.
        '''
        # pylint: disable=C0123
        src = self._src or self
        return Queryable(src, self._provider, query)

    def where(self, func):
        return self.update_query(self._query.where(func))

    def select(self, func):
        return self.update_query(self._query.select(func))

    def select_many(self, collection_selector=identity, result_selector=identity):
        return self.update_query(self._query.select_many(collection_selector, result_selector))

    def take(self, count: int):
        return self.update_query(self._query.take(count))

    def skip(self, count: int):
        return self.update_query(self._query.skip(count))

    def to_memory(self):
        '''
        force iter in memory.
        '''
        return self.update_query(self._query.to_memory())

    def get_reduce_info(self):
        '''
        print reduce info in console.
        '''
        return self._provider.get_reduce_info(self)


class QueryProvider(IQueryProvider):

    def _execute_in_memory(self, queryable: Queryable):
        if queryable.src is None:
            # when src is None, mean queryable is root.
            # the provider should implement this
            raise NotImplementedError('cannot execute query from None')
        fn = queryable.query.compile()
        return fn(queryable.src)
