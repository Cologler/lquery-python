# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the common visitor for database
# ----------

from ..expr import Make, AttrExpr, BinaryExpr, IndexExpr, ParameterExpr
from ..expr.visitor import DefaultExprVisitor


class DbExprVisitor(DefaultExprVisitor):
    '''
    provide many method for rewrite expr, but you need to manual call it.
    '''
    def rewrite_attr_expr_to_index_expr(self, expr: AttrExpr):
        '''
        rewrite `expr.name` => `expr['name']`
        '''
        expr_body = expr.expr.accept(self)
        return Make.index(expr_body, Make.const(expr.name))

    def rewrite_add_prefix_has_item(self, expr: BinaryExpr):
        '''
        rewrite `expr['name'] == 1` => `'name' in expr and expr['name'] == 1`
        '''
        if isinstance(expr.left, IndexExpr):
            return Make.binary_op(
                Make.binary_op(
                    expr.left.key,
                    'in',
                    expr.left.expr
                ),
                'and',
                expr
            )
        return expr

    def is_get_from_parameter(self, expr):
        '''
        test is match `x => x(['n']|n)...`
        '''
        if not isinstance(expr, (IndexExpr, AttrExpr)):
            return False
        if isinstance(expr, ParameterExpr):
            return True
        return self.is_get_from_parameter(expr.expr)
