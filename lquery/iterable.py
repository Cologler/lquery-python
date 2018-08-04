# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# queryable for Iterable
# ----------

from typing import Union
from collections import Iterable

from typeguard import typechecked

from .expr import CallExpr, ValueExpr, Make
from .func import NOT_QUERYABLE_FUNCS
from .queryable import Queryable, QueryProvider, IQueryable, ReduceInfo, QueryableSource

def get_result(expr):
    if type(expr) is CallExpr:
        args = [get_result(e) for e in expr.args]
        func = expr.func
        assert expr.args and not expr.kwargs
        return func(*args)
    else:
        return expr.value


class IterableQuery3(Queryable):
    def __init__(self, expr):
        super().__init__(expr, PROVIDER)

    def __iter__(self):
        return iter(get_result(self.expr))

    def update_reduce_info(self, reduce_info):
        reduce_info.add_node(ReduceInfo.TYPE_MEMORY, self.expr)


class IterableQuery(QueryableSource):
    @typechecked
    def __init__(self, items: Iterable):
        super().__init__(Make.ref(items), PROVIDER)

    def __str__(self):
        return f'Queryable({self.expr.value})'

    def __iter__(self):
        return iter(get_result(self.expr))


class IterableQueryProvider(QueryProvider):

    def create_query(self, src, query=None):
        queryable = IterableQuery(src)
        if query:
            for expr in query.exprs:
                queryable = self.execute(queryable, expr)
        return queryable

    def execute(self, expr: Union[ValueExpr, CallExpr]):
        if isinstance(expr, CallExpr):
            if expr.func in NOT_QUERYABLE_FUNCS:
                return get_result(expr)
        return IterableQuery3(expr)

PROVIDER = IterableQueryProvider()
