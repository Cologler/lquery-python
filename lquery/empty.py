# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a empty queryable
# ----------

from .func import NOT_QUERYABLE_FUNCS
from .queryable import Queryable, ReduceInfo, get_exprs, get_prev_queryable
from .iterable import IterableQueryProvider

class EmptyQuery(Queryable):
    def __init__(self, expr, reason=''):
        super().__init__(expr, PROVIDER)
        self._reason = reason

    def __iter__(self):
        yield from ()

    @property
    def reason(self):
        return self._reason


class EmptyQueryProvider(IterableQueryProvider):

    def get_reduce_info(self, queryable: EmptyQuery) -> ReduceInfo:
        '''
        get reduce info in console.
        '''
        info = ReduceInfo(queryable)
        info.set_mode(ReduceInfo.MODE_EMPTY, queryable.reason)
        for expr in get_exprs(queryable.expr):
            info.add_node(ReduceInfo.TYPE_NOT_EXEC, expr)
        return info

    def execute(self, expr):
        if expr.func in NOT_QUERYABLE_FUNCS:
            return super().execute(expr)
        return EmptyQuery(expr, get_prev_queryable(expr).reason)


PROVIDER = EmptyQueryProvider()
