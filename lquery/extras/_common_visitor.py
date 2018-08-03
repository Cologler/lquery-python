# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the common visitor for database
# ----------

from ..expr import Make, AttrExpr
from ..expr.visitor import DefaultExprVisitor


class DbExprVisitor(DefaultExprVisitor):
    '''
    provide many method for rewrite expr, but you need to manual call it.
    '''
    def rewrite_attr_expr_to_index_expr(self, expr: AttrExpr):
        '''
        rewrite `expr.name` => `expr['name']`
        '''
        return Make.index(expr.expr, Make.const(expr.name))
