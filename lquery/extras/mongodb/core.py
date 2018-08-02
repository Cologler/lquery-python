# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from ...func import where, skip, take
from ...query import Query
from ...queryable import Queryable, QueryProvider, ReduceInfo
from ...expr import (
    BinaryExpr, IndexExpr, ConstExpr, CallExpr, Expr,
    ParameterExpr,
    BuildDictExpr, BuildListExpr
)
from ...expr_builder import to_lambda_expr
from ...expr_utils import (
    get_deep_indexes,
    require_argument,
)
from ...iterable import PROVIDER as ITERABLE_PROVIDER
from ...iterable import IterableQuery

from .._common import NotSupportError, AlwaysEmptyError

from .options import QueryOptions, QueryOptionsUpdater


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
        self._exprs_in_sql = []
        self._exprs_in_memory = []
        self._query_options = QueryOptions()

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
            reduce_info.set_mode(ReduceInfo.MODE_EMPTY, self._always_empty.reason)
            for expr in self._queryable.query.exprs:
                reduce_info.add_node(ReduceInfo.TYPE_NOT_EXEC, expr)
        else:
            for expr in self._exprs_in_sql:
                reduce_info.add_node(ReduceInfo.TYPE_SQL, expr)
            for expr in self._exprs_in_memory:
                reduce_info.add_node(ReduceInfo.TYPE_MEMORY, expr)
        return reduce_info

    def _build_query(self):
        '''
        build self._query.
        '''
        assert self._query is None
        collection = self._mongodb_query.collection
        if collection is None:
            raise ValueError('cannot query with None collection')
        if self._always_empty:
            self._query = ()
        else:
            cursor = self._query_options.get_cursor(collection)
            query = IterableQuery(cursor)
            self._query = ITERABLE_PROVIDER.create_query(query, Query(*self._exprs_in_memory))
        return self._query

    def _apply_call(self, expr: CallExpr) -> bool:
        func = expr.func
        try:
            if func is where:
                self._apply_call_where(expr.args[1].value)
            elif func is skip:
                self._apply_call_skip(expr.args[1].value)
            elif func is take:
                self._apply_call_take(expr.args[1].value)
            return True
        except NotSupportError:
            return False
        except AlwaysEmptyError as always_empty:
            self._always_empty = always_empty
            return False

    def _apply_call_skip(self, value):
        QueryOptionsUpdater.add_skip(value).apply(self._query_options)

    def _apply_call_take(self, value):
        if value == 0:
            raise AlwaysEmptyError(f'only take {value} item')
        QueryOptionsUpdater.add_limit(value).apply(self._query_options)

    def _apply_call_where(self, predicate):
        # mongo find() only accept one filter and a limit after it
        # if `limit` is not None, cannot add more predicate.
        if self._query_options.limit is not None or self._query_options.skip is not None:
            raise NotSupportError

        lambda_expr = to_lambda_expr(predicate)
        if lambda_expr and len(lambda_expr.args) == 1:
            updater = self._get_updater_by_call_where(lambda_expr.body)
            updater.apply(self._query_options)
            return
        raise NotSupportError

    def _get_updater_by_call_where(self, body: Expr):
        if isinstance(body, BinaryExpr):
            return self._get_updater_by_call_where_binary(body)
        raise NotSupportError

    def _get_updater_by_call_where_binary(self, body: BinaryExpr):
        left, op, right = body.left, body.op, body.right
        if op in ('&', 'and'):
            lupdater = self._get_updater_by_call_where(left)
            rupdater = self._get_updater_by_call_where(right)
            return lupdater & rupdater
        else:
            return self._get_updater_by_call_where_compare(left, right, op)

    _SWAPABLE_OP_MAP = {
        '==': '==',
        '>': '<',
        '<': '>',
        '>=': '<=',
        '<=': '>=',

        # magic
        'in': '-in',
    }

    def _get_updater_by_call_where_compare(self, left, right, op):
        left_is_index_expr = isinstance(left, IndexExpr)
        right_is_index_expr = isinstance(right, IndexExpr)

        if not left_is_index_expr and not right_is_index_expr:
            raise NotSupportError
        if left_is_index_expr and right_is_index_expr:
            raise NotSupportError

        if not left_is_index_expr:
            swaped_op = self._SWAPABLE_OP_MAP.get(op)
            if swaped_op is None:
                raise NotSupportError
            return self._get_updater_by_call_where_compare(right, left, swaped_op)

        if isinstance(right, ConstExpr):
            value = right.value
        elif isinstance(right, BuildDictExpr):
            value = right.create()
        elif isinstance(right, BuildListExpr):
            value = right.create()
        elif isinstance(right, CallExpr):
            if require_argument(right):
                raise NotSupportError
            value = right()
        else:
            raise NotSupportError

        if isinstance(value, tuple):
            # python will auto convert `lambda x: x in ['A', 'B']` to `lambda x: x in ('A', 'B')`
            value = list(value)
        if not isinstance(value, (str, int, dict, list)):
            raise NotSupportError

        value = self._from_op(value, op)
        if value is None:
            raise NotSupportError
        indexes, src_expr = get_deep_indexes(left)
        if not isinstance(src_expr, ParameterExpr):
            # since where args == 1, this must be the element.
            raise NotSupportError
        fname = '.'.join(indexes)
        updater = QueryOptionsUpdater.add_filter_field(fname, value)
        return updater

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
        if op is None:
            raise NotSupportError

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
