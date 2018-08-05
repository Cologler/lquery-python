# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import copy

from ...func import where, skip, take
from ...queryable import Queryable, ReduceInfo
from ...iterable import IterableQueryProvider
from ...expr import (
    Make,
    BinaryExpr, IndexExpr, ValueExpr, CallExpr, Expr, AttrExpr,
    ParameterExpr,
    BuildDictExpr, BuildListExpr
)
from ...expr.builder import to_func_expr
from ...expr.utils import (
    get_deep_names,
    require_argument,
)
from ...expr.visitor import DefaultExprVisitor
from ...empty import EmptyQuery

from .._common import NotSupportError, AlwaysEmptyError

from .options import QueryOptions, QueryOptionsUpdater


VISITOR = DefaultExprVisitor()


class NextMongoDbQuery(Queryable):
    def __init__(self, expr, collection, query_options):
        super().__init__(expr, PROVIDER)
        self._collection = collection
        self._query_options = query_options or QueryOptions()

    def __str__(self):
        return f'Queryable({self._collection})'

    def __iter__(self):
        cursor = self._query_options.get_cursor(self._collection)
        yield from cursor

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


class MongoDbQueryQueryOptionsModifier:
    def __init__(self, query_options):
        self._accept_sql_query = True
        self._query = None
        self._always_empty = False
        self._query_options = query_options

    @property
    def always_empty(self):
        return self._always_empty

    def apply_call(self, expr: CallExpr) -> bool:
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

        lambda_expr = to_func_expr(predicate)
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
        left, op, right = body.left.accept(VISITOR), body.op, body.right.accept(VISITOR)
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
        left_is_prop_expr = isinstance(left, (IndexExpr, AttrExpr))
        right_is_prop_expr = isinstance(right, (IndexExpr, AttrExpr))

        if not left_is_prop_expr and not right_is_prop_expr:
            raise NotSupportError
        if left_is_prop_expr and right_is_prop_expr:
            raise NotSupportError

        if not left_is_prop_expr:
            swaped_op = self._SWAPABLE_OP_MAP.get(op)
            if swaped_op is None:
                raise NotSupportError
            return self._get_updater_by_call_where_compare(right, left, swaped_op)

        if isinstance(right, ValueExpr):
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
        indexes, src_expr = get_deep_names(left)
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


class MongoDbQueryProvider(IterableQueryProvider):
    def execute(self, expr):
        if expr.func in (where, skip, take):
            queryable = expr.args[0].value
            query_options = queryable.query_options
            query_options = copy.deepcopy(query_options)
            impl = MongoDbQueryQueryOptionsModifier(query_options)
            apply = impl.apply_call(expr)
            if impl.always_empty:
                return EmptyQuery(expr, impl.always_empty.reason)
            if apply:
                return NextMongoDbQuery(expr, queryable.collection, query_options)
        return super().execute(expr)


PROVIDER = MongoDbQueryProvider()
