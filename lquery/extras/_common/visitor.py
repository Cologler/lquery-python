# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the common visitor for database
# ----------

from ...expr import Make, AttrExpr, ExprType
from ...expr.visitor import DefaultExprVisitor


class DbExprVisitor(DefaultExprVisitor):
    '''
    provide many method for rewrite expr, but you need to manual call it.
    '''
    def rewrite_attr_expr_to_index_expr(self, expr: AttrExpr):
        '''
        rewrite `expr.name` => `expr['name']`
        '''
        assert expr.type == ExprType.Attr
        expr_body = expr.expr.accept(self)
        return Make.index(expr_body, Make.const(expr.name))

    def is_get_deep_indexes_from_parameter(self, expr):
        '''
        test is match `arg['a']['b']...`
        '''
        if not expr.type == ExprType.Index:
            return False
        if not expr.key.type == ExprType.Const:
            return False
        if expr.expr.type == ExprType.Parameter:
            return True
        return self.is_get_deep_indexes_from_parameter(expr.expr)
