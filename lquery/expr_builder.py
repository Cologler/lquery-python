# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import dis
from contextlib import contextmanager

from .expr import (
    CallExpr, # for type check
    attr, index, BinaryExpr, parameter, lambda_, make
)

DEBUG = False

@contextmanager
def debug():
    global DEBUG
    DEBUG = True
    yield
    DEBUG = False

class NotSupportError(Exception):
    def __init__(self, instr: dis.Instruction):
        self._instr = instr
        msg = f'not supported instruction: {instr}'
        super().__init__(msg)


class ExprBuilder:
    def __init__(self, func):
        self._func = func
        self._bytecode = dis.Bytecode(self._func)
        self._args = dict((n, parameter(n)) for n in self._bytecode.codeobj.co_varnames)
        self._stack = []
        self._instructions = list(self._bytecode)
        self._instructions_map = dict((v.offset, v) for v in self._instructions)

    def build(self):
        for instr in self._instructions:
            method_name = instr.opname.lower()
            method = getattr(self, method_name, None)
            if not method:
                raise NotSupportError(instr)
            method(instr)
        assert len(self._stack) == 1
        return self._stack.pop()

    def load_fast(self, instr: dis.Instruction):
        # load var
        self._stack.append(self._args[instr.argval])

    def load_const(self, instr: dis.Instruction):
        self._stack.append(instr.argval)

    def load_attr(self, instr: dis.Instruction):
        s = self._stack.pop()
        self._stack.append(attr(s, instr.argval))

    def binary_subscr(self, instr: dis.Instruction):
        # index like a[b]
        k = self._stack.pop()
        s = self._stack.pop()
        self._stack.append(index(s, k))

    def binary_add(self, instr: dis.Instruction):
        right = self._stack.pop()
        left = self._stack.pop()
        self._stack.append(BinaryExpr(make(left), make(right), '+'))

    def binary_and(self, instr: dis.Instruction):
        right = self._stack.pop()
        left = self._stack.pop()
        self._stack.append(BinaryExpr(make(left), make(right), '&'))

    def compare_op(self, instr: dis.Instruction):
        right = self._stack.pop()
        left = self._stack.pop()
        self._stack.append(BinaryExpr(make(left), make(right), instr.argval))

    def return_value(self, instr: dis.Instruction):
        # ignore.
        pass


def to_lambda_expr(expr: CallExpr):
    '''
    try compile a call expr to a lambda expr.

    return `None` when convert fail.
    '''
    if not isinstance(expr, CallExpr):
        raise TypeError
    if expr.kwargs:
        raise NotImplementedError
    try:
        body = ExprBuilder(expr.func).build()
    except NotSupportError as err:
        if DEBUG:
            print(err)
        return None
    if DEBUG:
        print('expr: ', body)
    return lambda_(body, *expr.args, **expr.kwargs)
