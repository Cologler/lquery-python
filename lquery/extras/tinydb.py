# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# lquery for tinydb
# ----------

from ..queryable import AbstractQueryable
from ..funcs import LinqQuery
from ..iterable import IterableQueryProvider
from ..expr import Make, ExprType
from ..expr.builder import to_func_expr
from ..expr.emitter import emit
from ..expr.utils import get_deep_indexes

from ._common_visitor import DbExprVisitor


class TinyDbQuery(AbstractQueryable):
    def __init__(self, table):
        super().__init__(Make.ref(table), PROVIDER)


class TinyDbQueryProvider(IterableQueryProvider):
    def create_query(self, expr):
        expr = self._get_rewrited_call_expr(expr) or expr
        return super().create_query(expr)

    def _get_rewrited_call_expr(self, call_expr):
        func = call_expr.func.resolve_value()
        if func is LinqQuery.where:
            func_expr = to_func_expr(call_expr.args[1].value)
            if func_expr is None:
                return
            expr = func_expr.accept(_TinyDb1ExprVisitor())
            expr = expr.accept(_TinyDb2ExprVisitor())
            print(expr)
            if expr is func_expr:
                return
            compiled_func = emit(expr)
            if compiled_func is None:
                return
            return Make.call(Make.ref(func), call_expr.args[0], Make.ref(compiled_func))


class _TinyDb1ExprVisitor(DbExprVisitor):
    '''
    use for convert attr to index expr
    '''
    def visit_attr_expr(self, expr):
        expr = super().visit_attr_expr(expr)
        if expr.type == ExprType.Attr:
            if expr.expr.type == ExprType.Parameter:
                if expr.name != 'doc_id':
                    expr = self.rewrite_attr_expr_to_index_expr(expr)
            elif self.is_get_deep_indexes_from_parameter(expr.expr):
                expr = self.rewrite_attr_expr_to_index_expr(expr)
        return expr


class _TinyDb2ExprVisitor(DbExprVisitor):
    '''
    use for convert

    `lambda x: x['a']['b'] == 1`

    to

    `lambda x: 'a' in x and 'b' in x['a'] and x['a']['b'] == 1`
    '''
    def visit_binary_expr(self, expr):
        print(f'visit_binary_expr:{expr}')
        expr = super().visit_binary_expr(expr)
        if expr.left.type == ExprType.Index:
            indexes, src = get_deep_indexes(expr.left)
            if src.type == ExprType.Parameter:
                cur_expr = expr
                src_expr = expr.left
                for index in reversed(indexes):
                    src_expr = src_expr.expr
                    cur_expr = self.rewrite_add_prefix_has_item(index, src_expr, cur_expr)
                return cur_expr
        return expr

    def rewrite_add_prefix_has_item(self, key, src, expr):
        return Make.binary_op(
            Make.binary_op(
                key,
                'in',
                src
            ),
            'and',
            expr
        )

PROVIDER = TinyDbQueryProvider()

def patch():
    '''
    '''
    from tinydb.database import Table
    if not hasattr(Table, 'query'):
        def query(self):
            return TinyDbQuery(self)
        Table.query = query
