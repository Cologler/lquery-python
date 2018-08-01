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
    attr, index, BinaryExpr, parameter, lambda_, make,
    build_dict, build_list
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
        self._args = [parameter(n) for n in self._bytecode.codeobj.co_varnames]
        self._args_map = dict((p.name, p) for p in self._args)
        self._stack = []
        self._instructions = list(self._bytecode)
        self._instructions_map = dict((v.offset, v) for v in self._instructions)

    def _print_stack(self):
        print(self._stack)

    def build(self):
        for instr in self._instructions:
            method_name = instr.opname.lower()
            method = getattr(self, method_name, None)
            if not method:
                raise NotSupportError(instr)
            method(instr)
        assert len(self._stack) == 1
        body = self._stack.pop()
        expr = lambda_(body, *self._args)
        return expr

    def load_fast(self, instr: dis.Instruction):
        # load argument
        self._stack.append(self._args_map[instr.argval])

    def load_const(self, instr: dis.Instruction):
        self._stack.append(instr.argval)

    def load_attr(self, instr: dis.Instruction):
        s = self._stack.pop()
        self._stack.append(attr(s, instr.argval))

    def load_deref(self, instr: dis.Instruction):
        # load from closure
        closure = self._func.__closure__[instr.arg]
        cell_contents = closure.cell_contents
        self._stack.append(cell_contents)

    def binary_subscr(self, _: dis.Instruction):
        # index like a[b]
        k = self._stack.pop()
        s = self._stack.pop()
        self._stack.append(index(s, k))

    def binary_add(self, _: dis.Instruction):
        right = self._stack.pop()
        left = self._stack.pop()
        self._stack.append(BinaryExpr(make(left), make(right), '+'))

    def binary_and(self, _: dis.Instruction):
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

    def build_list(self, instr: dis.Instruction):
        items = self._stack[-instr.arg:]
        self._stack = self._stack[0:-instr.arg]
        expr = build_list(*items)
        self._stack.append(expr)

    def build_const_key_map(self, _: dis.Instruction):
        kvps = []
        keys_tuple = self._stack.pop()
        keys = list(keys_tuple)
        while keys:
            k = keys.pop()
            v = self._stack.pop()
            kvps.append((k, v))
        kvps.reverse()
        expr = build_dict(*kvps)
        self._stack.append(expr)


def to_lambda_expr(func):
    '''
    try compile a call expr to a lambda expr.

    return `None` when convert fail.
    '''
    assert callable(func)
    try:
        expr = ExprBuilder(func).build()
    except NotSupportError as err:
        if DEBUG:
            print(err)
        return None
    if DEBUG:
        print('expr: ', expr)
    return expr
