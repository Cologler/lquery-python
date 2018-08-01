# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a htlper module for expr.
# ----------

from .expr import (
    IExpr,
    ParameterExpr, ConstExpr, AttrExpr, IndexExpr, BinaryExpr, CallExpr, LambdaExpr
)

def get_deep_indexes(index_expr: IndexExpr):
    '''
    for example:

    `IndexExpr(x.a['size']['h'])` -> `['size', 'h'], AttrExpr(x.a)`.
    '''
    fields = []
    cur_expr = index_expr
    while isinstance(cur_expr, IndexExpr):
        fields.append(cur_expr.name)
        cur_expr = cur_expr.expr
    fields.reverse()
    return fields, cur_expr

def require_argument(expr: IExpr) -> bool:
    '''
    check is the `expr` reference or use argument to do some thing.
    '''
    expr_type = type(expr)
    if expr_type is ParameterExpr:
        return True
    if expr_type is ConstExpr:
        return False
    if expr_type in (AttrExpr, IndexExpr):
        return require_argument(expr.expr)
    if expr_type is BinaryExpr:
        return require_argument(expr_type.left) or require_argument(expr_type.right)
    if expr_type is CallExpr:
        return any(require_argument(a) for a in list(expr.args) + list(expr.kwargs.values()))
    if expr_type is LambdaExpr:
        raise NotImplementedError
    raise NotImplementedError('any others ?')
