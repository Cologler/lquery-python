# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from ..func import where, skip, take
from ..query import Query
from ..queryable import Queryable, QueryProvider
from ..expr import (
    BinaryExpr, IndexExpr, ConstExpr, call, parameter, CallExpr, Expr,
    BuildDictExpr, BuildListExpr
)
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
        self._always_empty = False
        self._filter = {}
        self._skip = None
        self._limit = None

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
            cursor = self._mongodb_query.collection.find(
                filter=self._filter,
                skip=self._skip or 0,
                limit=self._limit or 0)
        self._query = IterableQuery(cursor)
        return self._query

    def _apply_call(self, expr: CallExpr) -> bool:
        func = expr.func
        if func is where:
            return self._apply_call_where(expr.args[1].value)
        if func is skip:
            return self._apply_call_skip(expr.args[1].value)
        if func is take:
            return self._apply_call_take(expr.args[1].value)
        # for unhandled call, return False to create memory query.
        return False

    def _apply_call_skip(self, value):
        if self._skip is None:
            self._skip = value
        else:
            self._skip += value
        return True

    def _apply_call_take(self, value):
        if value == 0:
            self._always_empty = True
        elif self._limit is None:
            self._limit = value
        else:
            self._limit = min(self._limit, value)
        return True

    def _apply_call_where(self, predicate):
        # mongo find() only accept one filter and a limit after it
        # if `limit` is not None, cannot add more predicate.
        if self._limit is not None or self._skip is not None:
            return False

        lambda_expr = to_lambda_expr(call(predicate, parameter('_')))
        if lambda_expr:
            return self._apply_call_where_by(lambda_expr.body)
        return False

    def _apply_call_where_by(self, body: Expr):
        if isinstance(body, BinaryExpr):
            return self._apply_call_where_binary(body)
        return False

    def _apply_call_where_binary(self, body: BinaryExpr):
        left, op, right = body.left, body.op, body.right
        if op == '&':
            if not self._apply_call_where_by(left):
                return False
            if not self._apply_call_where_by(right):
                return False
            return True
        return self._apply_call_where_compare(left, right, op)

    def _apply_call_where_compare(self, left, right, op):
        left_is_index_expr = isinstance(left, IndexExpr)
        right_is_index_expr = isinstance(right, IndexExpr)

        if not left_is_index_expr and not right_is_index_expr:
            return False
        if left_is_index_expr and right_is_index_expr:
            return False

        if not left_is_index_expr:
            return self._apply_call_where_compare(right, left, op)

        if isinstance(right, ConstExpr):
            value = right.value
        elif isinstance(right, BuildDictExpr):
            value = right.create()
        elif isinstance(right, BuildListExpr):
            value = right.create()
        else:
            return False

        if not isinstance(value, (str, int, dict, list)):
            return False

        value = self._from_op(value, op)
        if value is None:
            return False
        data = self._filter
        fname = '.'.join(self._from_deep_fields(left))
        if data.get(fname, value) != value:
            self._always_empty = True
        else:
            data[fname] = value
        return True

    def _from_deep_fields(self, left_expr: IndexExpr):
        '''
        for `x['size']['h']` typed expr, return `['size', 'h']`.
        '''
        fields = []
        cur_expr = left_expr
        while isinstance(cur_expr.expr, IndexExpr):
            fields.append(cur_expr.name)
            cur_expr = cur_expr.expr
        fields.append(cur_expr.name)
        fields.reverse()
        return fields

    OP_MAP = {
        '<': '$lt',
        '>': '$gt',
    }

    def _from_op(self, right_value, op):
        '''
        get mongodb query object value by `value` and `op`.

        for example: `(3, '>')` => `{ '$gt': 3 }`
        '''
        if op == '==' or op == 'in':
            # in mean item in list
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
