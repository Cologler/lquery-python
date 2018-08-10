# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import enum
import abc
from typing import List, Dict, Callable, Tuple

from typeguard import typechecked

# errors

class RequireArgumentError(Exception):
    '''
    a error for describe `resolve_value()` failed.
    '''
    pass


# interfaces

class ExprType(enum.Enum):
    Parameter = 2
    Const = 3
    Reference = 4
    Deref = 5
    Attr = 6
    Index = 7
    Unary = 8
    Binary = 9
    Call = 10
    Func = 11
    BuildList = 31
    BuildDict = 32


class IExpr:
    __slots__ = ()

    @abc.abstractproperty
    def type(self):
        '''
        return a enum `ExprType`.
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def accept(self, visitor):
        '''
        accept a visitor as selector.
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def resolve_value(self):
        '''
        try resolve value from static expr tree.

        if expr tree require parameters, raise `RequireArgumentError`.
        '''
        raise NotImplementedError

# base classes

class Expr(IExpr):
    __slots__ = ()

    def accept(self, visitor):
        return visitor.visit(self)


class ValueExpr(Expr):
    '''
    the base class for both of `ConstExpr` and `ReferenceExpr`.
    '''
    __slots__ = ('_value')

    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    def __str__(self):
        return repr(self.resolve_value())

    def __repr__(self):
        return f'{type(self).__name__}({repr(self.resolve_value())})'

    def resolve_value(self):
        return self._value

# classes


class ParameterExpr(Expr):
    '''
    represents raw input parameter.
    '''
    __slots__ = ('_name')

    @typechecked
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._name

    def __repr__(self):
        return f'ParameterExpr({repr(self._name)})'

    @property
    def type(self):
        return ExprType.Parameter

    def accept(self, visitor):
        return visitor.visit_parameter_expr(self)

    def resolve_value(self):
        raise RequireArgumentError


class ConstExpr(ValueExpr):
    '''
    represents value expr for immutable object.
    '''
    __slots__ = ()

    @property
    def type(self):
        return ExprType.Const

    def accept(self, visitor):
        return visitor.visit_const_expr(self)


class ReferenceExpr(ValueExpr):
    '''
    represents value expr for both of immutable and mutable object.
    '''
    __slots__ = ()

    @property
    def type(self):
        return ExprType.Reference

    def accept(self, visitor):
        return visitor.visit_reference_expr(self)


class DerefExpr(Expr):
    '''
    represents value expr for closure variable.
    '''
    __slots__ = ('_cell')

    def __init__(self, cell):
        super().__init__()
        self._cell = cell

    def __str__(self):
        return repr(self.resolve_value())

    def __repr__(self):
        return f'DerefExpr({repr(self.resolve_value())})'

    @property
    def type(self):
        return ExprType.Deref

    def accept(self, visitor):
        return visitor.visit_deref_expr(self)

    def resolve_value(self):
        return self._cell.cell_contents


class AttrExpr(Expr):
    '''
    represents `expr.attr`.
    '''
    __slots__ = ('_expr', '_name')

    @typechecked
    def __init__(self, expr: IExpr, name: str):
        self._expr = expr
        self._name = name

    @property
    def expr(self):
        return self._expr

    @property
    def name(self):
        return self._name

    def __str__(self):
        return f'{str(self._expr)}.{self._name}'

    def __repr__(self):
        return f'AttrExpr({repr(self._expr)}, {repr(self._name)})'

    @property
    def type(self):
        return ExprType.Attr

    def accept(self, visitor):
        return visitor.visit_attr_expr(self)

    def resolve_value(self):
        return getattr(self._expr.resolve_value(), self._name)


class AssignExpr(Expr):
    '''
    represents `target = value`.
    '''
    __slots__ = ('_target', '_value')

    def __init__(self, target: AttrExpr, value: IExpr):
        super().__init__()
        self._target = target
        self._value = value

    @property
    def target(self):
        return self._target

    @property
    def value(self):
        return self._value

    def __str__(self):
        return f'{self._target} = {self._value}'

    def __repr__(self):
        return f'AssignExpr({repr(self._target)}, {repr(self._value)})'


class IndexExpr(Expr):
    '''
    represents `expr[name]`.
    '''
    __slots__ = ('_expr', '_key')

    @typechecked
    def __init__(self, expr: IExpr, key: IExpr):
        self._expr = expr
        self._key = key

    @property
    def expr(self):
        return self._expr

    @property
    def key(self):
        return self._key

    @property
    def name(self):
        return self._key

    def __str__(self):
        return f'{self._expr}[{self._key}]'

    def __repr__(self):
        return f'IndexExpr({repr(self._expr)}, {repr(self._key)})'

    @property
    def type(self):
        return ExprType.Index

    def accept(self, visitor):
        return visitor.visit_index_expr(self)

    def resolve_value(self):
        return self._expr.resolve_value()[self._key.resolve_value()]


class UnaryExpr(Expr):
    __slots__ = ('_expr', '_op')

    @typechecked
    def __init__(self, expr: IExpr, op: str):
        self._expr = expr
        self._op = op

    @property
    def expr(self):
        return self._expr

    @property
    def op(self):
        return self._op

    def __str__(self):
        op = self._op
        return f'{op} ({str(self._expr)})'

    def __repr__(self):
        return f'UnaryExpr({repr(self._op)}, {repr(self._expr)})'

    @property
    def type(self):
        return ExprType.Unary

    def accept(self, visitor):
        return visitor.visit_unary_expr(self)


class BinaryExpr(Expr):
    __slots__ = ('_left', '_right', '_op')

    OP_MAP = {
        '__eq__': '==',
        '__gt__': '>',
        '__lt__': '<',
        '__ge__': '>=',
        '__le__': '<=',
        '__and__': '&',
        '__or__': '|',
    }

    @typechecked
    def __init__(self, left: IExpr, op: str, right: IExpr):
        self._left = left
        self._right = right
        self._op = op

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    @property
    def op(self):
        return self._op

    def __str__(self):
        op = self.OP_MAP.get(self._op, self._op)
        return f'{str(self._left)} {op} {str(self._right)}'

    def __repr__(self):
        return f'BinaryExpr({repr(self._left)}, {repr(self._op)}, {repr(self._right)})'

    @property
    def type(self):
        return ExprType.Binary

    def accept(self, visitor):
        return visitor.visit_binary_expr(self)


class CallExpr(Expr):
    __slots__ = ('_func', '_args', '_kwargs')

    def __init__(self, func: IExpr, *args: List[IExpr], **kwargs: Dict[str, IExpr]):
        # all item of args and value of kwargs are union(ValueExpr, ParameterExpr)
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    @property
    def func(self):
        return self._func

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    def __str__(self):
        return self.to_str()

    def to_str(self, *, is_method=False) -> str:
        fn = str(self._func)
        args = self._args[1:] if is_method else self._args
        ls = [str(x) for x in args]
        ls += [f'{k}={v}' for k, v in self._kwargs.items()]
        args_str = ', '.join(ls)
        return f'{fn}({args_str})'

    def __call__(self):
        return self.resolve_value()

    def __repr__(self):
        exprs = [repr(self._func)]
        exprs.extend([repr(a) for a in self._args])
        exprs.extend([f'k={repr(v)}' for k, v in self._kwargs.items()])
        inside = ', '.join(exprs)
        return f'CallExpr({inside})'

    @property
    def type(self):
        return ExprType.Call

    def accept(self, visitor):
        return visitor.visit_call_expr(self)

    def resolve_value(self):
        args = [v.resolve_value() for v in self._args]
        kwargs = dict((k, v.resolve_value()) for k, v in self._kwargs.items())
        return self._func.resolve_value()(*args, **kwargs)


class FuncExpr(Expr):
    __slots__ = ('_body', '_args')

    def __init__(self, body : IExpr, *args: List[IExpr]):
        super().__init__()
        self._body = body
        self._args = args

    @property
    def body(self):
        return self._body

    @property
    def args(self):
        return self._args

    def __str__(self):
        args_str = ', '.join(str(x) for x in self._args)
        return f'lambda {args_str}: {self._body}'

    def __repr__(self):
        return f'FuncExpr({repr(self._body)}, {repr(self._args)})'

    @property
    def type(self):
        return ExprType.Func

    def accept(self, visitor):
        return visitor.visit_func_expr(self)


class BuildListExpr(Expr):
    __slots__ = ('_items')

    def __init__(self, *items: List[ValueExpr]):
        self._items = items

    @property
    def items(self):
        return self._items

    def __str__(self):
        items_str = ', '.join(f'{repr(v)}' for v in self._items)
        return f'[{items_str}]'

    def __repr__(self):
        items_str = ', '.join(f'{repr(v)}' for v in self._items)
        return f'BuildListExpr({items_str})'

    @property
    def type(self):
        return ExprType.BuildList

    def resolve_value(self):
        return [x.resolve_value() for x in self._items]


class BuildDictExpr(Expr):
    __slots__ = ('_kvps')

    def __init__(self, *kvps: List[Tuple[ValueExpr, ValueExpr]]):
        self._kvps = kvps

    @property
    def kvps(self):
        return self._kvps

    def __str__(self):
        kvps_str = ', '.join(f'{repr(k.value)}: {repr(v.value)}' for k, v in self._kvps)
        return f'{{{kvps_str}}}'

    @property
    def type(self):
        return ExprType.BuildDict

    def resolve_value(self):
        d = {}
        for k, v in self._kvps:
            d[k.resolve_value()] = v.resolve_value()
        return d

class Make:
    @staticmethod
    def ref(value):
        return ReferenceExpr(value)

    @staticmethod
    def const(value):
        return ConstExpr(value)

    @staticmethod
    def deref(cell):
        return DerefExpr(cell)

    @staticmethod
    def call(func: IExpr, *args: List[IExpr], **kwargs: Dict[str, IExpr]):
        '''
        create a expr for represents call a function.
        '''
        return CallExpr(func, *args, **kwargs)

    @staticmethod
    def parameter(name: str):
        '''
        create a expr for represents a parameter.
        '''
        return ParameterExpr(name)

    @staticmethod
    def binary_op(left: IExpr, op: str, right: IExpr):
        '''
        create a expr for represents a binary operation.
        '''
        return BinaryExpr(left, op, right)

    @staticmethod
    def unary_op(expr: IExpr, op: str):
        return UnaryExpr(expr, op)

    @staticmethod
    def attr(expr: IExpr, name: str):
        return AttrExpr(expr, name)

    @staticmethod
    def assign(target: IExpr, value: IExpr):
        return AssignExpr(target, value)

    @staticmethod
    def index(expr: IExpr, key: IExpr):
        return IndexExpr(expr, key)

    @staticmethod
    def build_dict(*kvps):
        return BuildDictExpr(*kvps)

    @staticmethod
    def build_list(*items):
        return BuildListExpr(*items)

    @staticmethod
    def func(body : IExpr, *args: List[IExpr]):
        return FuncExpr(body, *args)
