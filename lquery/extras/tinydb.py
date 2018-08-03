# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# lquery for tinydb
# ----------

from ..func import NOT_QUERYABLE_FUNCS, where
from ..queryable import Queryable, QueryProvider
from ..expr import Make
from ..expr.builder import to_func_expr
from ..expr.emiter import emit

from ._common_visitor import DbExprVisitor


class TinyDbQuery(Queryable):
    def __init__(self, table):
        super().__init__(None, PROVIDER)
        self._table = table

    def __iter__(self):
        yield from self._table


class TinyDbQueryProvider(QueryProvider):
    def execute(self, queryable, call_expr):
        if call_expr.func in NOT_QUERYABLE_FUNCS:
            return super().execute(queryable, call_expr)
        call_expr = self._get_rewrited_call_expr(call_expr) or call_expr
        return super().execute(queryable, call_expr)

    def _get_rewrited_call_expr(self, call_expr):
        if call_expr.func is where:
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
            return Make.call(where, call_expr.args[0], Make.ref(compiled_func))


class TinyDbExprVisitor(DbExprVisitor):

    def visit_attr_expr(self, expr):
        if expr.name == 'doc_id':
            # not convert
            return expr
        return self.rewrite_attr_expr_to_index_expr(expr)


PROVIDER = TinyDbQueryProvider()
