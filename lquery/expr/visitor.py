# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .core import Make, ConstExpr

class ExprVisitor:
    def visit(self, expr):
        return expr

    def visit_attr_expr(self, expr):
        return self.visit(expr)

    def visit_index_expr(self, expr):
        return self.visit(expr)

    def visit_call_expr(self, expr):
        return self.visit(expr)

    def visit_func_expr(self, expr):
        return self.visit(expr)

    def visit_unary_expr(self, expr):
        return self.visit(expr)

    def visit_binary_expr(self, expr):
        return self.visit(expr)

    def visit_parameter_expr(self, expr):
        return self.visit(expr)

    def visit_const_expr(self, expr):
        return self.visit(expr)

    def visit_reference_expr(self, expr):
        return self.visit(expr)

    def visit_deref_expr(self, expr):
        return self.visit(expr)


class DefaultExprVisitor(ExprVisitor):

    def visit_attr_expr(self, expr):
        src_expr = expr.expr.accept(self)
        if src_expr is expr.expr:
            return expr
        return Make.attr(src_expr, expr.name)

    def visit_index_expr(self, expr):
        src_expr = expr.expr.accept(self)
        key_expr = expr.key.accept(self)
        if src_expr is expr.expr and key_expr is expr.key:
            return expr
        return Make.attr(src_expr, expr.name)

    def visit_call_expr(self, expr):
        if expr.func.resolve_value() is getattr:
            if len(expr.args) == 2 and not expr.kwargs:
                attr_expr = expr.args[1]
                if isinstance(attr_expr, ConstExpr) and isinstance(attr_expr.value, str):
                    return Make.attr(expr.args[0], attr_expr.value)
        return expr

    def visit_binary_expr(self, expr):
        left = expr.left.accept(self)
        right = expr.right.accept(self)
        if left is expr.left and right is expr.right:
            return expr
        return Make.binary_op(left, expr.op, right)

    def visit_func_expr(self, expr):
        body = expr.body.accept(self)
        if body is not expr.body:
            return Make.func(body, *expr.args)
        return expr


class ValueResolverExprVisitor(ExprVisitor):
    def visit(self, expr):
        return expr.resolve_value()


class ExprsIterExprVisitor(ExprVisitor):
    def visit(self, expr):
        yield expr

    def visit_attr_expr(self, expr):
        yield expr
        yield from expr.expr.accept(self)

    def visit_index_expr(self, expr):
        yield expr
        yield from expr.expr.accept(self)
        yield from expr.key.accept(self)

    def visit_call_expr(self, expr):
        yield expr
        expr_list = list(expr.args) + list(expr.kwargs.values())
        for e in expr_list:
            yield from e.accept(self)

    def visit_func_expr(self, expr):
        raise NotImplementedError

    def visit_unary_expr(self, expr):
        yield expr
        yield from expr.expr.accept(self)

    def visit_binary_expr(self, expr):
        yield expr
        yield from expr.left.accept(self)
        yield from expr.right.accept(self)
