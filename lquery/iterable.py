# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# queryable for Iterable
# ----------

from collections import Iterable

from typeguard import typechecked

from .queryable import Queryable, QueryProvider, IQueryable, ReduceInfo, EMPTY_QUERYS

class IterableQuery(Queryable):
    @typechecked
    def __init__(self, items: Iterable):
        super().__init__(None, PROVIDER, EMPTY_QUERYS)
        self._items = items

    def __iter__(self):
        return iter(self._items)

    def __str__(self):
        return f'Queryable({str(self._items)})'


class IterableQuery2(Queryable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reduced_func = None

    def __iter__(self):
        reduced_func = self._compile()
        return iter(reduced_func(self.src))

    def _compile(self):
        '''
        compile the query as memory call.
        '''
        if self._reduced_func is None:
            expr = self.expr
            args = [expr.value for expr in expr.args[1:]]
            func = expr.func
            assert expr.args and not expr.kwargs
            def _func(src):
                return func(src, *args)
            self._reduced_func = _func
        return self._reduced_func


class IterableQueryProvider(QueryProvider):

    def create_query(self, src, query=None):
        queryable = IterableQuery(src)
        if query:
            for expr in query.exprs:
                queryable = self.then_query(queryable, expr)
        return queryable

    def get_reduce_info(self, queryable: IQueryable) -> ReduceInfo:
        '''
        get reduce info in console.
        '''
        if queryable.src:
            info: ReduceInfo = queryable.src.get_reduce_info()
        else:
            info = ReduceInfo(queryable)
        if queryable.expr:
            info.add_node(ReduceInfo.TYPE_MEMORY, queryable.expr)
        return info

    def execute(self, queryable: Queryable):
        yield from queryable

    def then_query(self, queryable: Queryable, query_expr):
        querys = queryable.querys.then(query_expr)
        return IterableQuery2(queryable, self, querys)

PROVIDER = IterableQueryProvider()
