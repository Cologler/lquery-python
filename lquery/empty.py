# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a empty queryable
# ----------

from .func import NOT_QUERYABLE_FUNCS
from .queryable import Queryable, ReduceInfo, get_exprs, get_prev_queryable
from .iterable import IterableQueryProvider

class EmptyReduceInfo(ReduceInfo):
    def __init__(self, queryable, reason):
        super().__init__(queryable)
        self._reason = reason

    @property
    def mode(self):
        return self.MODE_EMPTY

    def get_desc_strs(self):
        return [f'all query was skiped since always empty: {self._mode_reason}']


class EmptyQuery(Queryable):
    def __init__(self, expr, reason=''):
        super().__init__(expr, PROVIDER)
        self._reason = reason

    def __iter__(self):
        yield from ()

    @property
    def reason(self):
        return self._reason

    def get_reduce_info(self):
        '''
        get reduce info in console.
        '''
        info = EmptyReduceInfo(self, self._reason)
        for expr in get_exprs(self.expr):
            info.add_node(ReduceInfo.TYPE_NOT_EXEC, expr)
        return info


class EmptyQueryProvider(IterableQueryProvider):
    def execute(self, expr):
        if expr.func in NOT_QUERYABLE_FUNCS:
            return super().execute(expr)
        return EmptyQuery(expr, get_prev_queryable(expr).reason)


PROVIDER = EmptyQueryProvider()
