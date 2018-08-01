# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from ..func import where
from ..query import Query
from ..queryable import Queryable, QueryProvider
from ..expr import BinaryExpr, IndexExpr, ConstExpr, call, parameter, CallExpr
from ..expr_builder import to_lambda_expr
from ..iterable import PROVIDER as ITERABLE_PROVIDER
from ..iterable import IterableQuery

class MongoDbQuery(Queryable):
    def __init__(self, collection):
        super().__init__(None, PROVIDER)
        self._collection = collection

    @property
    def collection(self):
        return self._collection


class MongoDbQueryImpl:
    def __init__(self, queryable: Queryable):
        self._mongodb_query = queryable.src or queryable
        self._query = None
        self._filter = {}
        self._always_empty = False

        exprs = []
        for expr in queryable.query.exprs:
            if self._query is None and not self._apply_call(expr):
                self._build_query()
            if self._query is not None:
                exprs.append(expr)
        query = self._query or self._build_query()
        self._query = ITERABLE_PROVIDER.create_query(query, Query(*exprs))

    def __iter__(self):
        return iter(self._query)

    def _build_query(self):
        # build query for in-memory query
        if self._always_empty:
            cursor = []
        else:
            cursor = self._mongodb_query.collection.find(self._filter)
        self._query = IterableQuery(cursor)
        return self._query

    def _apply_call(self, expr: CallExpr) -> bool:
        func = expr.func
        if func is where:
            return self._apply_call_where(expr.args[1].value)

        # for unhandled call, return False to create memory query.
        return False

    def _apply_call_where(self, predicate):
        lambda_expr = to_lambda_expr(call(predicate, parameter('_')))
        if lambda_expr:
            body = lambda_expr.body
            if isinstance(body, BinaryExpr):
                left, op, right = body.left, body.op, body.right
                return self._apply_call_where_compare(left, right, op)
        return False

    def _apply_call_where_compare(self, left, right, op):
        if isinstance(right, IndexExpr) and isinstance(left, ConstExpr):
            return self._apply_call_where_compare(right, left, op)
        if isinstance(left, IndexExpr) and isinstance(right, ConstExpr):
            if isinstance(right.value, (str, int)):
                value = self._from_op(right.value, op)
                if value is not None:
                    if self._filter.get(left.name, value) != value:
                        self._always_empty = True
                    else:
                        self._filter[left.name] = value
                    return True
        return False

    OP_MAP = {
        '<': '$lt',
        '>': '$gt',
    }

    def _from_op(self, right_value, op):
        if op == '==':
            return right_value
        op = self.OP_MAP.get(op)
        if op is not None:
            return {
                op: right_value
            }


class MongoDbQueryProvider(QueryProvider):

    def execute(self, queryable: Queryable):
        return MongoDbQueryImpl(queryable)


PROVIDER = MongoDbQueryProvider()
