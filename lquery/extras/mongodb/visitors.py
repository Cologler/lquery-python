# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import re

from ...funcs import LinqQuery
from ...expr import (
    RequireArgumentError,
    BinaryExpr, IndexExpr, CallExpr, AttrExpr, UnaryExpr,
    ParameterExpr
)
from ...expr.builder import to_func_expr
from ...expr.visitor import DefaultExprVisitor, ExprVisitor
from ...expr.utils import get_deep_names

from .._common import NotSupportError, AlwaysEmptyError

from .options import QueryOptionsUpdater


VISITOR = DefaultExprVisitor()


class QueryOptionsExprVisitor(ExprVisitor):
    def __init__(self, query_options):
        self._query_options = query_options

    def visit(self, expr):
        raise NotSupportError

    def _get_parameter_indexes(self, expr):
        indexes, base_expr = get_deep_names(expr)
        if not isinstance(base_expr, ParameterExpr):
            # since where args == 1, this must be the element.
            raise NotSupportError
        return '.'.join(indexes)


class QueryOptionsRootExprVisitor(QueryOptionsExprVisitor):

    def visit_call_expr(self, expr: CallExpr) -> bool:
        func = expr.func.resolve_value()
        if func is LinqQuery.where:
            return self._apply_call_where(expr.args[1].value)
        elif func is LinqQuery.skip:
            return self._apply_call_skip(expr.args[1].value)
        elif func is LinqQuery.take:
            return self._apply_call_take(expr.args[1].value)
        raise NotSupportError

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
            visitor = QueryOptionsCallWhereExprVisitor(self._query_options)
            updater = lambda_expr.body.accept(visitor)
            updater.apply(self._query_options)
            return
        raise NotSupportError


class QueryOptionsCallWhereExprVisitor(QueryOptionsExprVisitor):
    def visit_index_expr(self, expr: IndexExpr):
        indexes = self._get_parameter_indexes(expr)
        return QueryOptionsUpdater.filter_field(indexes)

    def visit_attr_expr(self, expr: AttrExpr):
        indexes = self._get_parameter_indexes(expr)
        return QueryOptionsUpdater.filter_field(indexes)

    def visit_unary_expr(self, expr: UnaryExpr):
        updater = expr.expr.accept(self)
        return updater.op_unary(expr.op)

    def visit_binary_expr(self, body: BinaryExpr):
        left, op, right = body.left.accept(VISITOR), body.op, body.right.accept(VISITOR)
        if op in ('&', 'and'):
            lupdater = left.accept(self)
            rupdater = right.accept(self)
            return lupdater & rupdater
        else:
            return self._get_updater_by_compare(left, right, op)

    _SWAPABLE_OP_MAP = {
        '==': '==',
        '!=': '!=',
        '>': '<',
        '<': '>',
        '>=': '<=',
        '<=': '>=',

        # magic
        'in': '-in',
        'not in': '-not in',
    }

    def _resolve_value(self, expr):
        try:
            value = expr.resolve_value()
            return True, value
        except RequireArgumentError:
            return False, None

    def _get_updater_by_compare(self, left, right, op):
        lh, lv = self._resolve_value(left)
        rh, rv = self._resolve_value(right)
        if lh == rh:
            # both has arguments or not
            raise NotSupportError
        if lh:
            op = self._SWAPABLE_OP_MAP.get(op)
            if op is None:
                raise NotSupportError
            expr = right
            value = lv
        else:
            expr = left
            value = rv

        if isinstance(value, tuple):
            # python will auto convert `lambda x: x in ['A', 'B']` to `lambda x: x in ('A', 'B')`
            value = list(value)
        if not isinstance(value, (str, int, dict, list)):
            raise NotSupportError

        updater = expr.accept(self)
        return updater.op_binary(op, value)

    def visit_call_expr(self, expr: CallExpr):
        # re.search('?', doc.name)
        func = expr.func.resolve_value()
        print(func is re.search)
        if func is re.search:
            return self._get_updater_by_re_search(expr)
        if func is hasattr:
            return self._get_updater_by_hasattr(expr)
        raise NotSupportError

    def _get_updater_by_re_search(self, expr: CallExpr):
        if len(expr.args) == 2:
            pattern = expr.args[0].resolve_value()
            field_name = self._get_parameter_indexes(expr.args[1])
            return QueryOptionsUpdater.add_filter_field(field_name, {'$regex': pattern})
        raise NotSupportError

    def _get_updater_by_hasattr(self, expr: CallExpr):
        field_name = self._get_parameter_indexes(expr.args[0])
        field_name = f'{field_name}.{expr.args[1].resolve_value()}'
        return QueryOptionsUpdater.filter_field_exists(field_name)
