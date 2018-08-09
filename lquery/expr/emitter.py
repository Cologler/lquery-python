# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a func expr emiter
# ----------

from bytecode.cfg import ControlFlowGraph
from bytecode import (
    Instr, Compare, FreeVar, Label
)

from .core import ConstExpr

class ByteCodeEmitter:
    def __init__(self, func_expr):
        self._src_expr = func_expr
        self._cells = []

        self._bytecode = ControlFlowGraph()
        self._bytecode.name = str(func_expr)
        self._bytecode.argcount = len(self._src_expr.args)
        self._bytecode.argnames = [x.name for x in self._src_expr.args]
        self._bytecode.freevars = ['<cell>']
        self._block_0 = self._bytecode[0]
        self._block = self._block_0 # current block

    def _print_blocks(self):
        for bi, block in enumerate(self._bytecode):
            print(f'block {bi}:')
            for i in range(len(block)):
                print(f'    {block[i]}')

    def emit(self, *, debug=False):
        try:
            self.on_expr(self._src_expr.body)
            self._block.append(Instr('RETURN_VALUE'))
            if debug:
                self._print_blocks()
            code = self._bytecode.to_bytecode().to_code()
            cell = tuple(self._cells)
            def compiled_func():
                return cell # so compiled_func has a free var: (cell, )
            compiled_func.__name__ = f'<{self._src_expr}>'
            compiled_func.__code__ = code
            return compiled_func
        except NotImplementedError:
            if debug:
                import traceback
                traceback.print_exc()
                for instr in self._block:
                    print(instr)
            return None

    def on_expr(self, expr):
        method_name = 'on_' + type(expr).__name__.lower()
        method = getattr(self, method_name)
        return method(expr)

    def on_parameterexpr(self, expr):
        self._block.append(Instr("LOAD_FAST", expr.name))

    def on_constexpr(self, expr):
        self._block.append(Instr("LOAD_CONST", expr.value))

    def on_referenceexpr(self, expr):
        self._block.append(Instr("LOAD_DEREF", FreeVar('<cell>')))
        self._block.append(Instr("LOAD_CONST", len(self._cells)))
        self._block.append(Instr("BINARY_SUBSCR"))
        self._cells.append(expr.value)

    def on_derefexpr(self, expr):
        self._block.append(Instr("LOAD_DEREF", FreeVar('<cell>')))
        self._block.append(Instr("LOAD_CONST", len(self._cells)))
        self._block.append(Instr("BINARY_SUBSCR"))
        self._cells.append(expr) # lazy load value
        self._block.append(Instr("LOAD_ATTR", 'value'))

    def on_attrexpr(self, expr):
        self.on_expr(expr.expr)
        self._block.append(Instr("LOAD_ATTR", expr.name))

    def on_indexexpr(self, expr):
        self.on_expr(expr.expr)
        self.on_expr(expr.key)
        self._block.append(Instr("BINARY_SUBSCR"))

    _OP_MAP = {
        '<':    Compare.LT,
        '<=':   Compare.LE,
        '==':   Compare.EQ,
        '!=':   Compare.NE,
        '>':    Compare.GT,
        '>=':   Compare.GE,
        'in':   Compare.IN,
        'not in': Compare.NOT_IN,
        'is':   Compare.IS,
        'is not': Compare.IS_NOT,
        '':     Compare.EXC_MATCH,
    }

    def on_binaryexpr(self, expr):
        if expr.op in self._OP_MAP:
            self.on_expr(expr.left)
            self.on_expr(expr.right)
            self._block.append(Instr("COMPARE_OP", self._OP_MAP[expr.op]))
        elif expr.op in ('and', 'or'):
            self.on_expr(expr.left)
            block_left = self._block
            block_right = self._bytecode.add_block()
            self._block = block_right
            self.on_expr(expr.right)
            if not self._block:
                # like a and (b and c), has a empty block can reuse.
                block_end = self._block
            else:
                block_end = self._bytecode.add_block()
            if expr.op == 'and':
                block_left.append(Instr('JUMP_IF_FALSE_OR_POP', block_end))
            else:
                block_left.append(Instr('JUMP_IF_TRUE_OR_POP', block_end))
            self._block = block_end
        else:
            raise NotImplementedError(f'not impl op: {expr.op}')

    def on_callexpr(self, expr):
        raise NotImplementedError

    def on_buildlistexpr(self, expr):
        for item in expr.items:
            self._block.append(Instr("LOAD_CONST", item.value))
        self._block.append(Instr("BUILD_LIST", len(expr.items)))

    def on_builddictexpr(self, expr):
        if all(isinstance(k, ConstExpr) for k, v in expr.kvps):
            # BUILD_CONST_KEY_MAP
            for _, v in expr.kvps:
                self.on_expr(v)
            self._block.append(Instr("LOAD_CONST", tuple([k.value for k, v in expr.kvps])))
            self._block.append(Instr('BUILD_CONST_KEY_MAP', len(expr.kvps)))
            return
        raise NotImplementedError


def emit(func_expr, *, debug=False):
    '''
    return `None` if emit failed.
    '''
    emiter = ByteCodeEmitter(func_expr)
    return emiter.emit(debug=debug)
