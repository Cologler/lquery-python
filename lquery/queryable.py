# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod, abstractproperty
from typing import Union, List
from collections import namedtuple

from typeguard import typechecked

from .expr import Make, CallExpr, ValueExpr
from .utils import wrap_fast_fail
from .extendable import Extendable


class IQueryProvider:

    '''
    interface of `QueryProvider`
    '''
    @abstractmethod
    def execute(self, expr: Union[ValueExpr, CallExpr]):
        '''
        return a `IQueryable` or a value by `expr`.

        for example, if the `expr.func.resolve_value()` is `count`, return value should be a number.
        '''
        raise NotImplementedError


class IQueryable(Extendable):
    '''
    interface of `Queryable`
    '''

    @abstractproperty
    def expr(self) -> Union[ValueExpr, CallExpr]:
        raise NotImplementedError

    @abstractproperty
    def provider(self) -> IQueryProvider:
        raise NotImplementedError

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError('you should implement the query in subclass.')

    @classmethod
    def extend_linq(cls, return_queryable: bool, name: str = None):
        '''
        allow user add extension methods for `IQueryable`.

        method will be wrap as `CallExpr`.
        '''
        def _(func):
            # set the `return_queryable`
            func.return_queryable = bool(return_queryable)

            method_name = name or func.__name__
            @wrap_fast_fail(func)
            def wraped_func(self, *args, **kwargs):
                args_list = list(args)
                call_args = [func, self] + args_list
                args_expr = [Make.ref(a) for a in call_args]
                kwargs_expr = dict([(k, Make.ref(v)) for k, v in kwargs.items()])
                next_expr = Make.call(*args_expr, **kwargs_expr)
                return self.provider.execute(next_expr)
            cls._extend(method_name, wraped_func)
            return func
        return _


ReduceInfoNode = namedtuple('ReduceInfoNode', ['type', 'expr'])


class ReduceInfo:
    # pylint: disable=C0326
    TYPE_SRC        = 0
    TYPE_MEMORY     = 1
    TYPE_SQL        = 2
    TYPE_NOT_EXEC   = 3

    MODE_NORMAL     = 21
    # the query has conflict, so the result always are empty.
    MODE_EMPTY      = 22
    # pylint: enable=C0326

    _PRINT_TABLE = {
        0: 'SRC',
        1: 'MEM',
        2: 'SQL',
        3: ''
    }

    def __init__(self, queryable: IQueryable):
        self.querable = queryable # need to set from stack top.
        self._details: List[ReduceInfoNode] = []

    def add_node(self, type_, expr):
        self._details.append(ReduceInfoNode(type_, expr))

    @property
    def mode(self):
        return self.MODE_NORMAL

    @property
    def details(self):
        return self._details[:]

    def get_desc_strs(self):
        strs = []
        if all(d.type == self.TYPE_MEMORY for d in self.details):
            strs = ['all exec in memory']
        elif all(d.type == self.TYPE_SQL for d in self.details):
            strs = ['all exec in SQL']
        else:
            strs = []
            for type_, expr in self.details:
                expr_str = None
                if isinstance(expr, CallExpr):
                    expr_str = expr.to_str(is_method=True)
                else:
                    expr_str = str(expr.value)
                strs.append(f'[{self._PRINT_TABLE[type_]}] {expr_str}')
        return strs

    def print(self):
        desc_strs = self.get_desc_strs()
        reduce_info_str = '\n'.join('    ' + line for line in desc_strs)
        print(f'reduce info of:\n  {self.querable}\n=>\n{reduce_info_str}')


class AbstractQueryable(IQueryable):
    @typechecked
    def __init__(self, expr: Union[ValueExpr, CallExpr], provider: IQueryProvider):
        self._expr = expr
        self._provider = provider

    @property
    def expr(self):
        return self._expr

    @property
    def provider(self) -> IQueryProvider:
        return self._provider

    def __str__(self):
        expr = self.expr
        exprs = [expr]
        while isinstance(expr, CallExpr):
            expr = expr.args[0].value.expr
            exprs.append(expr)
        exprs.reverse()
        lines = [f'IQueryable({repr(exprs[0].value)})']
        for expr in exprs[1:]:
            lines.append(expr.to_str(is_method=True))
        return '\n    .'.join(lines)

    def get_reduce_info(self):
        '''
        print reduce info in console.
        '''
        reduce_info = ReduceInfo(self)
        for queryable in get_queryables(self.expr):
            queryable.update_reduce_info(reduce_info)
        self.update_reduce_info(reduce_info)
        return reduce_info

    def update_reduce_info(self, reduce_info: ReduceInfo):
        pass


def get_queryables(expr):
    '''
    get queryables chain as a `tuple`.
    '''
    queryables = []
    while isinstance(expr, CallExpr):
        queryables.append(expr.args[0].value)
        expr = queryables[-1].expr
    # the first (<ValueExpr>expr).value is src, which should not be the queryable.
    queryables.reverse()
    return tuple(queryables)

def get_prev_queryable(expr):
    '''
    get previous queryable.
    '''
    if isinstance(expr, CallExpr):
        return expr.args[0].value
    return expr.value

def get_exprs(expr):
    exprs = []
    while isinstance(expr, CallExpr):
        exprs.append(expr)
        expr = exprs[-1].args[0].value.expr
    exprs.append(expr)
    return tuple(reversed(exprs))
