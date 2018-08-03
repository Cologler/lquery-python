# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .core import ValueExpr, AttrExpr

class ExprVisitor:
    def visit(self, expr):
        return expr

    def visit_call_expr(self, expr):
        return expr


class DefaultExprVisitor(ExprVisitor):
    def visit_call_expr(self, expr):
        if expr.func is getattr:
            if len(expr.args) == 2 and not expr.kwargs:
                attr_expr = expr.args[1]
                if isinstance(attr_expr, ValueExpr) and isinstance(attr_expr.value, str):
                    return AttrExpr(expr.args[0], attr_expr.value)
        return expr
