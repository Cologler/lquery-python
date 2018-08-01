# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a htlper module for expr.
# ----------

from .expr import IndexExpr

def get_deep_indexes(left_expr: IndexExpr):
    '''
    for example:

    `IndexExpr(x.a['size']['h'])` -> `['size', 'h'], AttrExpr(x.a)`.
    '''
    fields = []
    cur_expr = left_expr
    while isinstance(cur_expr, IndexExpr):
        fields.append(cur_expr.name)
        cur_expr = cur_expr.expr
    fields.reverse()
    return fields, cur_expr
