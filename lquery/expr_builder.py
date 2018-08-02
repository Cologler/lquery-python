# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import dis
from contextlib import contextmanager

from .expr import (
    attr, index, BinaryExpr, parameter, lambda_, make, call,
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
    def __init__(self, *, msg=None, instr: dis.Instruction=None):
        if instr:
            msg = msg or f'not supported instruction: {instr}'
        super().__init__(msg or '')


class ExprBuilder:
    def __init__(self, func):
        self._func = func
        self._bytecode = dis.Bytecode(self._func)
        self._args = [parameter(n) for n in self._bytecode.codeobj.co_varnames]
        self._args_map = dict((p.name, p) for p in self._args)
        self._stack = []
        self._instructions = list(self._bytecode)
        self._instructions_map = dict((v.offset, v) for v in self._instructions)
        self._instructions_hooks = {}

    def _print_stack(self):
        print('expr-builder-stack:', self._stack)

    def _not_support(self, *, msg=None, instr: dis.Instruction=None):
        if DEBUG:
            self._print_stack()
        raise NotSupportError(msg=msg, instr=instr)

    def _stack_pop(self, count):
        if count > 0:
            items = self._stack[-count:]
            self._stack = self._stack[0:-count]
            return items
        else:
            return []

    def _hook(self, offset, callback):
        hooks = self._instructions_hooks.get(offset)
        if not hooks:
            self._instructions_hooks[offset] = hooks = []
        hooks.append(callback)

    def build(self):
        for instr in self._instructions:
            hooks = self._instructions_hooks.get(instr.offset)
            if hooks:
                for callback in reversed(hooks):
                    callback()
                del self._instructions_hooks[instr.offset]
            method_name = instr.opname.lower()
            method = getattr(self, method_name, None)
            if not method:
                return self._not_support(instr=instr)
            method(instr)
        if len(self._stack) != 1:
            return self._not_support(msg='unknwon return values.')
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

    def load_global(self, instr: dis.Instruction):
        name = instr.argval
        if name in self._func.__globals__:
            self._stack.append(self._func.__globals__[name])
            return
        builtins = self._func.__globals__['__builtins__']
        if name in builtins:
            self._stack.append(builtins[name])
            return
        return self._not_support(instr=instr)

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
        items = self._stack_pop(instr.arg)
        expr = build_list(*items)
        self._stack.append(expr)

    def build_const_key_map(self, _: dis.Instruction):
        keys = self._stack.pop()
        kvps = list(zip(keys, self._stack_pop(len(keys))))
        expr = build_dict(*kvps)
        self._stack.append(expr)

    def call_function(self, instr: dis.Instruction):
        args = self._stack_pop(instr.arg)
        func = self._stack.pop()
        expr = call(func, *args)
        self._stack.append(expr)

    def call_function_kw(self, _: dis.Instruction):
        keys = self._stack.pop()
        kvps = list(zip(keys, self._stack_pop(len(keys))))
        kwargs = dict(kvps)
        func = self._stack.pop()
        expr = call(func, **kwargs)
        self._stack.append(expr)

    def pop_top(self, _: dis.Instruction):
        # opcode=1
        self._stack.pop()

    def rot_two(self, _: dis.Instruction):
        # opcode=2
        node = self._stack.pop()
        self._stack.insert(-1, node)

    def rot_three(self, _: dis.Instruction):
        # opcode=3
        node = self._stack.pop()
        self._stack.insert(-2, node)

    def dup_top(self, _: dis.Instruction):
        # opcode=4
        self._stack.append(self._stack[-1])

    def jump_if_false_or_pop(self, instr: dis.Instruction):
        # opcode=111
        # If TOS is false, sets the bytecode counter to target and leaves TOS on the stack.
        # Otherwise (TOS is true), TOS is popped.
        # mean `and`
        left = self._stack.pop()
        def callback():
            right = self._stack.pop()
            self._stack.append(BinaryExpr(make(left), make(right), 'and'))
        self._hook(instr.argval, callback)

    def jump_if_true_or_pop(self, instr: dis.Instruction):
        # opcode=112
        # If TOS is true, sets the bytecode counter to target and leaves TOS on the stack.
        # Otherwise (TOS is false), TOS is popped.
        # mean `or`
        left = self._stack.pop()
        def callback():
            right = self._stack.pop()
            self._stack.append(BinaryExpr(make(left), make(right), 'or'))
        self._hook(instr.argval, callback)


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
