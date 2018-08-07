# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import copy

from ...queryable import AbstractQueryable, ReduceInfo
from ...funcs import LinqQuery
from ...iterable import IterableQueryProvider
from ...expr import Make
from ...empty import EmptyQuery

from .._common import NotSupportError, AlwaysEmptyError

from .options import QueryOptions
from .visitors import QueryOptionsRootExprVisitor


class NextMongoDbQuery(AbstractQueryable):
    def __init__(self, expr, collection, query_options):
        super().__init__(expr, PROVIDER)
        self._collection = collection
        self._query_options = query_options or QueryOptions()

    def __str__(self):
        return f'IQueryable({self._collection})'

    def get_cursor(self):
        cursor = self._query_options.get_cursor(self._collection)
        return cursor

    def __iter__(self):
        yield from self.get_cursor()

    @property
    def collection(self):
        return self._collection

    @property
    def query_options(self):
        return self._query_options

    def update_reduce_info(self, reduce_info: ReduceInfo):
        reduce_info.add_node(ReduceInfo.TYPE_SQL, self.expr)


class MongoDbQuery(NextMongoDbQuery):
    def __init__(self, collection):
        super().__init__(Make.ref(collection), collection, QueryOptions())

    def update_reduce_info(self, reduce_info: ReduceInfo):
        reduce_info.add_node(ReduceInfo.TYPE_SRC, self.expr)


class MongoDbQueryProvider(IterableQueryProvider):
    def execute(self, expr):
        if expr.func.resolve_value() in (LinqQuery.where, LinqQuery.skip, LinqQuery.take):
            queryable = expr.args[0].value
            query_options = copy.deepcopy(queryable.query_options)
            visitor = QueryOptionsRootExprVisitor(query_options)
            try:
                expr.accept(visitor)
                return NextMongoDbQuery(expr, queryable.collection, query_options)
            except AlwaysEmptyError as always_empty:
                return EmptyQuery(expr, always_empty.reason)
            except NotSupportError:
                pass
        return super().execute(expr)


PROVIDER = MongoDbQueryProvider()









