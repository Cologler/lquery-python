# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a empty queryable
# ----------

from .queryable import Queryable, QueryProvider, ReduceInfo, EMPTY_QUERYS, ReduceInfo

class EmptyQuery(Queryable):
    def __init__(self, querys=EMPTY_QUERYS, reason='', **kwargs):
        super().__init__(None, PROVIDER, querys, **kwargs)
        self._reason = reason

    def __iter__(self):
        yield from ()

    @property
    def reason(self):
        return self._reason


class EmptyQueryProvider(QueryProvider):

    def get_reduce_info(self, queryable: EmptyQuery) -> ReduceInfo:
        '''
        get reduce info in console.
        '''
        info = ReduceInfo(queryable)
        info.set_mode(ReduceInfo.MODE_EMPTY, queryable.reason)
        for expr in queryable.querys.exprs:
            info.add_node(ReduceInfo.TYPE_NOT_EXEC, expr)
        return info

    def then_query(self, queryable: EmptyQuery, query_expr):
        querys = queryable.querys.then(query_expr)
        return EmptyQuery(querys, queryable.reason)


PROVIDER = EmptyQueryProvider()
