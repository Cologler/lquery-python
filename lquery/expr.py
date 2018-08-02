# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from enum import Enum
from typing import List

from typeguard import typechecked

class ExprType(Enum):
    Attr = 0


class IExpr:
    def accept(self, visitor):
        return visitor.visit(self)


class Expr(IExpr):
    pass


class EmptyExpr(Expr):
    pass


class ParameterExpr(Expr):
    '''
    represents raw input parameter.
    '''

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


class ConstExpr(Expr):
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    def __str__(self):
        return repr(self._value)

    def __repr__(self):
        return f'ParameterExpr({repr(self._value)})'


class AttrExpr(Expr):
    '''
    represents `expr.attr`.
    '''

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


class IndexExpr(Expr):
    '''
    represents `expr[name]`.
    '''

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
        return f'{str(self._expr)}[{repr(self._name)}]'

    def __repr__(self):
        return f'IndexExpr({repr(self._expr)}, {repr(self._name)})'


class BinaryExpr(Expr):
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
    def __init__(self, left: IExpr, right: IExpr, op: str):
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
        return f'BinaryExpr({repr(self._left)}, {repr(self._right)}, {repr(self._op)})'


class CallExpr(Expr):
    def __init__(self, func, *args, **kwargs):
        # all item of args and value of kwargs are ConstExpr
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
        fn = self._func.__name__
        args = self._args[1:] if is_method else self._args
        ls = [str(x) for x in args]
        ls += [f'{k}={repr(v)}' for k, v in self._kwargs.items()]
        args_str = ', '.join(ls)
        return f'{fn}({args_str})'

    def __call__(self):
        args = [v.value for v in self._args]
        kwargs = dict((k, self._kwargs[k].value) for k in self._kwargs)
        return self._func(*args, **kwargs)

    def accept(self, visitor):
        args = [x.accept(visitor) for x in self._args]
        kwargs = dict((k, self._kwargs[k].accept(visitor)) for k in self._kwargs)
        self_expr = CallExpr(self._func, *args, **kwargs)
        return visitor.visit_call_expr(self_expr)


class LambdaExpr(Expr):
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


class BuildListExpr(Expr):
    def __init__(self, *items):
        self._items = items

    @property
    def items(self):
        return self._items

    def __str__(self):
        kvps_str = ', '.join(f'{repr(v)}' for v in self._items)
        return f'[{kvps_str}]'

    def create(self):
        '''
        build the dict
        '''
        return list(self._items)


class BuildDictExpr(Expr):
    def __init__(self, *kvps):
        self._kvps = kvps

    @property
    def kvps(self):
        return self._kvps

    def __str__(self):
        kvps_str = ', '.join(f'{repr(k)}: {repr(v)}' for k, v in self._kvps)
        return f'{{{kvps_str}}}'

    def create(self):
        '''
        build the dict
        '''
        d = {}
        for k, v in self._kvps:
            d[k] = v
        return d


def make(obj) -> IExpr:
    if isinstance(obj, IExpr):
        return obj
    return const(obj)

def and_(left: IExpr, right: IExpr) -> IExpr:
    '''
    represents `left and right`
    '''
    return BinaryExpr(left, right, '__and__')

def or_(left: IExpr, right: IExpr) -> IExpr:
    '''
    represents `left or right`
    '''
    return BinaryExpr(left, right, '__or__')

def equal(left: IExpr, right: IExpr) -> IExpr:
    '''
    represents `left == right`
    '''
    return BinaryExpr(make(left), make(right), '==')

def greater_than(left: IExpr, right: IExpr, equals: bool = False) -> IExpr:
    '''
    represents `left > right` or `left >= right`
    '''
    op = '>' if equals else '>='
    return BinaryExpr(left, right, op)

def less_than(left: IExpr, right: IExpr, equals: bool = False) -> IExpr:
    '''
    represents `left < right` or `left <= right`
    '''
    op = '<' if equals else '<='
    return BinaryExpr(left, right, op)

def call(func, *args, **kwargs):
    '''
    represents call a function.
    '''
    return CallExpr(func, *[make(x) for x in args], **dict((k, make(kwargs[k])) for k in kwargs))

def build_dict(*kvps):
    '''
    represents build a dict object.
    '''
    return BuildDictExpr(*kvps)

def build_list(*items):
    '''
    represents build a dict object.
    '''
    return BuildListExpr(*items)

# pylint: disable=C0103
empty = EmptyExpr
parameter = ParameterExpr
const = ConstExpr
attr = AttrExpr
index = IndexExpr
lambda_ = LambdaExpr
