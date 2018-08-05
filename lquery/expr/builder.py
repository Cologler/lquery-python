# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import dis
from contextlib import contextmanager
from typing import List, Dict

from .core import IExpr, Make

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


class FuncExprBuilder:
    def __init__(self, func):
        self._func = func
        self._bytecode = dis.Bytecode(self._func)
        # create func arguments
        self._args: List[IExpr] = [Make.parameter(n) for n in self._bytecode.codeobj.co_varnames]
        self._args_map: Dict[str, IExpr] = dict((p.name, p) for p in self._args)

        self._stack: List[IExpr] = []
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
        expr = Make.func(body, *self._args)
        return expr

    def load_fast(self, instr: dis.Instruction):
        # load arguments
        self._stack.append(self._args_map[instr.argval])

    def load_const(self, instr: dis.Instruction):
        expr = Make.const(instr.argval)
        self._stack.append(expr)

    def load_deref(self, instr: dis.Instruction):
        # load from closure
        cell = self._func.__closure__[instr.arg]
        expr = Make.deref(cell)
        self._stack.append(expr)

    def load_global(self, instr: dis.Instruction):
        name = instr.argval
        if name in self._func.__globals__:
            expr = Make.ref(self._func.__globals__[name])
            self._stack.append(expr)
            return
        builtins = self._func.__globals__['__builtins__']
        if not isinstance(builtins, dict):
            builtins = vars(builtins)
        if name in builtins:
            expr = Make.ref(builtins[name])
            self._stack.append(expr)
            return
        return self._not_support(instr=instr)

    def compare_op(self, instr: dis.Instruction):
        right = self._stack.pop()
        left = self._stack.pop()
        expr = Make.binary_op(left, instr.argval, right)
        self._stack.append(expr)

    def return_value(self, instr: dis.Instruction):
        # ignore.
        pass

    def build_list(self, instr: dis.Instruction):
        items = self._stack_pop(instr.arg)
        expr = Make.build_list(*items)
        self._stack.append(expr)

    def build_const_key_map(self, _: dis.Instruction):
        keys_tuple = self._stack.pop().value
        keys = [Make.const(k) for k in keys_tuple]
        values = self._stack_pop(len(keys))
        kvps = list(zip(keys, values))
        expr = Make.build_dict(*kvps)
        self._stack.append(expr)

    def call_function(self, instr: dis.Instruction):
        args = self._stack_pop(instr.arg)
        func = self._stack.pop()
        expr = Make.call(func, *args)
        self._stack.append(expr)

    def call_function_kw(self, _: dis.Instruction):
        keys = self._stack.pop().value
        kvps = list(zip(keys, self._stack_pop(len(keys))))
        kwargs = dict(kvps)
        func = self._stack.pop()
        expr = Make.call(func, **kwargs)
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

    def _unary_op(self, op: str):
        expr = Make.unary_op(self._stack.pop(), op)
        self._stack.append(expr)

    def unary_not(self, _: dis.Instruction):
        # opcode=12
        self._unary_op('not')

    def _binary_op(self, op: str):
        right = self._stack.pop()
        left = self._stack.pop()
        expr = Make.binary_op(left, op, right)
        self._stack.append(expr)

    def binary_modulo(self, _: dis.Instruction):
        # opcode=23
        self._binary_op('%')

    def binary_add(self, _: dis.Instruction):
        # opcode=23
        self._binary_op('+')

    def binary_subtract(self, _: dis.Instruction):
        # opcode=24
        self._binary_op('-')

    def binary_subscr(self, _: dis.Instruction):
        # opcode=25
        # index like a[b]
        key = self._stack.pop()
        src = self._stack.pop()
        expr = Make.index(src, key)
        self._stack.append(expr)

    def binary_floor_divide(self, _: dis.Instruction):
        # opcode=26
        self._binary_op('//')

    def binary_true_divide(self, _: dis.Instruction):
        # opcode=27
        self._binary_op('/')

    def inplace_add(self, _: dis.Instruction):
        # opcode=55
        self._binary_op('+=')

    def inplace_subtract(self, _: dis.Instruction):
        # opcode=56
        self._binary_op('-=')

    def inplace_multiply(self, _: dis.Instruction):
        # opcode=57
        self._binary_op('*=')

    def binary_and(self, _: dis.Instruction):
        # opcode=64
        self._binary_op('&')

    def binary_or(self, _: dis.Instruction):
        # opcode=66
        self._binary_op('|')

    def load_attr(self, instr: dis.Instruction):
        # opcode=106
        src = self._stack.pop()
        expr = Make.attr(src, instr.argval)
        self._stack.append(expr)

    def jump_if_false_or_pop(self, instr: dis.Instruction):
        # opcode=111
        # If TOS is false, sets the bytecode counter to target and leaves TOS on the stack.
        # Otherwise (TOS is true), TOS is popped.
        # mean `and`
        left = self._stack.pop()
        def callback():
            right = self._stack.pop()
            expr = Make.binary_op(left, 'and', right)
            self._stack.append(expr)
        self._hook(instr.argval, callback)

    def jump_if_true_or_pop(self, instr: dis.Instruction):
        # opcode=112
        # If TOS is true, sets the bytecode counter to target and leaves TOS on the stack.
        # Otherwise (TOS is false), TOS is popped.
        # mean `or`
        left = self._stack.pop()
        def callback():
            right = self._stack.pop()
            expr = Make.binary_op(left, 'or', right)
            self._stack.append(expr)
        self._hook(instr.argval, callback)


def to_func_expr(func):
    '''
    try compile a `callable` to a lambda expr.

    return `None` when convert fail.
    '''
    assert callable(func)
    if DEBUG:
        print('parsing func: ', func)
    try:
        expr = FuncExprBuilder(func).build()
    except NotSupportError as err:
        if DEBUG:
            print(err)
        return None
    if DEBUG:
        print('str(expr) : ', expr)
        print('repr(expr): ', repr(expr))
    return expr
