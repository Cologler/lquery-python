# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from ..func import where, skip, take
from ..query import Query
from ..queryable import Queryable, QueryProvider, ReduceInfo
from ..expr import (
    BinaryExpr, IndexExpr, ConstExpr, call, parameter, CallExpr, Expr,
    ParameterExpr,
    BuildDictExpr, BuildListExpr
)
from ..expr_builder import to_lambda_expr
from ..expr_utils import (
    get_deep_indexes,
    require_argument,
)
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
        self._queryable = queryable
        self._mongodb_query = queryable.src or queryable

        self._accept_sql_query = True
        self._query = None
        self._always_empty = False
        self._always_empty_reason = None
        self._exprs_in_sql = []
        self._exprs_in_memory = []

        self._filter = {}
        self._skip = None
        self._limit = None

        for expr in queryable.query.exprs:
            self._accept_sql_query = self._accept_sql_query and self._apply_call(expr)
            if self._accept_sql_query:
                self._exprs_in_sql.append(expr)
            else:
                self._exprs_in_memory.append(expr)

    def __iter__(self):
        query = self._query or self._build_query()
        return iter(query)

    def get_reduce_info(self):
        reduce_info = ReduceInfo(self._queryable)
        if self._always_empty:
            reduce_info.set_mode(ReduceInfo.MODE_EMPTY, self._always_empty_reason)
            for expr in self._queryable.query.exprs:
                reduce_info.add_node(ReduceInfo.TYPE_NOT_EXEC, expr)
        else:
            for expr in self._exprs_in_sql:
                reduce_info.add_node(ReduceInfo.TYPE_SQL, expr)
            for expr in self._exprs_in_memory:
                reduce_info.add_node(ReduceInfo.TYPE_MEMORY, expr)
        return reduce_info

    def _set_always_empty(self, reason: str):
        self._always_empty = True
        self._always_empty_reason = reason

    def _build_query(self):
        # build query for in-memory query
        assert self._query is None
        if self._always_empty:
            self._query = ()
        else:
            cursor = self._mongodb_query.collection.find(
                filter=self._filter,
                skip=self._skip or 0,
                limit=self._limit or 0)
            query = IterableQuery(cursor)
            self._query = ITERABLE_PROVIDER.create_query(query, Query(*self._exprs_in_memory))
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
            self._set_always_empty('only take 0 item')
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

        lambda_expr = to_lambda_expr(predicate)
        if lambda_expr and len(lambda_expr.args) == 1:
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

    _SWAPABLE_OP_MAP = {
        '==': '==',
        '>': '<=',
        '<': '>=',
        '>=': '<',
        '<=': '>',

        # magic
        'in': '-in',
    }

    def _apply_call_where_compare(self, left, right, op):
        left_is_index_expr = isinstance(left, IndexExpr)
        right_is_index_expr = isinstance(right, IndexExpr)

        if not left_is_index_expr and not right_is_index_expr:
            return False
        if left_is_index_expr and right_is_index_expr:
            return False

        if not left_is_index_expr:
            swaped_op = self._SWAPABLE_OP_MAP.get(op)
            if swaped_op is None:
                return False
            return self._apply_call_where_compare(right, left, swaped_op)

        if isinstance(right, ConstExpr):
            value = right.value
        elif isinstance(right, BuildDictExpr):
            value = right.create()
        elif isinstance(right, BuildListExpr):
            value = right.create()
        elif isinstance(right, CallExpr):
            if require_argument(right):
                return False
            value = right()
        else:
            return False

        if isinstance(value, tuple):
            # python will auto convert `lambda x: x in ['A', 'B']` to `lambda x: x in ('A', 'B')`
            value = list(value)
        if not isinstance(value, (str, int, dict, list)):
            return False

        value = self._from_op(value, op)
        if value is None:
            return False
        data = self._filter
        indexes, src_expr = get_deep_indexes(left)
        if not isinstance(src_expr, ParameterExpr):
            # since where args == 1, this must be the element.
            return False
        fname = '.'.join(indexes)
        if data.get(fname, value) != value:
            return False
            self._set_always_empty(f'set {fname} multi times')
        else:
            data[fname] = value
        return True

    _OP_MAP = {
        '<': '$lt',
        '>': '$gt',
        '<=': '$lte',
        '>=': '$gte',
        'in': '$in',
    }

    def _from_op(self, right_value, op):
        '''
        get mongodb query object value by `value` and `op`.

        for example: `(3, '>')` => `{ '$gt': 3 }`
        '''
        if op == '==' or op == '-in':
            # in mean item in list
            return right_value

        op = self._OP_MAP.get(op)
        if op is not None:
            return {
                op: right_value
            }


class MongoDbQueryProvider(QueryProvider):

    def execute(self, queryable: Queryable):
        return MongoDbQueryImpl(queryable)

    def get_reduce_info(self, queryable: Queryable):
        impl = MongoDbQueryImpl(queryable)
        return impl.get_reduce_info()


PROVIDER = MongoDbQueryProvider()
