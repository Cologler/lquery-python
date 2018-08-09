# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# lquery for tinydb
# ----------

from ..queryable import AbstractQueryable
from ..funcs import LinqQuery
from ..iterable import IterableQueryProvider
from ..expr import Make, IndexExpr
from ..expr.builder import to_func_expr
from ..expr.emitter import emit

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
            visitor = TinyDbExprVisitor()
            expr = func_expr.accept(visitor)
            if expr is func_expr:
                return
            compiled_func = emit(expr)
            if compiled_func is None:
                return
            return Make.call(Make.ref(func), call_expr.args[0], Make.ref(compiled_func))


class TinyDbExprVisitor(DbExprVisitor):

    def visit_binary_expr(self, expr):
        expr = super().visit_binary_expr(expr)
        if isinstance(expr.left, IndexExpr):
            expr = self.rewrite_add_prefix_has_item(expr)
            return expr
        return expr

    def visit_attr_expr(self, expr):
        if expr.name == 'doc_id':
            # not convert
            return expr
        expr = self.rewrite_attr_expr_to_index_expr(expr)
        return expr


PROVIDER = TinyDbQueryProvider()

def patch():
    '''
    '''
    from tinydb.database import Table
    if not hasattr(Table, 'query'):
        def query(self):
            return TinyDbQuery(self)
        Table.query = query
