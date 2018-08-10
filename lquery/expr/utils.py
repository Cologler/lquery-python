# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a htlper module for expr.
# ----------

from typing import Union
from .core import (
    IExpr, ExprType,
    ParameterExpr, ConstExpr, ReferenceExpr, AttrExpr,
    IndexExpr, BinaryExpr, CallExpr, FuncExpr, ValueExpr
)
from .visitor import ExprsIterExprVisitor, ExprVisitor

def _get_attrs(expr, types, attr):
    fields = []
    cur_expr = expr
    while isinstance(cur_expr, types):
        fields.append(getattr(cur_expr, attr))
        cur_expr = cur_expr.expr
    fields.reverse()
    return fields, cur_expr

def get_deep_names(expr: Union[AttrExpr, IndexExpr]):
    fields = []
    cur_expr = expr
    while isinstance(cur_expr, (AttrExpr, IndexExpr)):
        if isinstance(cur_expr, AttrExpr):
            fields.append(cur_expr.name)
        elif isinstance(cur_expr.key, ValueExpr):
            fields.append(cur_expr.key.resolve_value())
        else:
            break
        cur_expr = cur_expr.expr
    fields.reverse()
    return fields, cur_expr

def get_deep_attrs(attr_expr: AttrExpr):
    return _get_attrs(attr_expr, AttrExpr, 'name')

def get_deep_indexes(index_expr: IndexExpr):
    '''
    for example:

    `IndexExpr(x.a['size']['h'])` -> `['size', 'h'], AttrExpr(x.a)`.
    '''
    indexes = []
    cur_expr = index_expr
    while cur_expr.type == ExprType.Index:
        indexes.append(cur_expr.key)
        cur_expr = cur_expr.expr
    indexes.reverse()
    return indexes, cur_expr


class RequireArgumentExprVisitor(ExprVisitor):
    def visit(self, expr):
        return False

    def visit_parameter_expr(self, expr):
        return True

def require_argument(expr: IExpr) -> bool:
    '''
    check is the `expr` reference or use argument to do some thing.
    '''
    visitor = RequireArgumentExprVisitor()
    for e in expr.accept(ExprsIterExprVisitor()):
        if e.accept(visitor):
            return True
    return False
