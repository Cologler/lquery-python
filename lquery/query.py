# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import Callable

from typeguard import typechecked

from .expr import parameter, call
from .func import where, select, take, skip, to_memory

class Query:
    def __init__(self, *exprs):
        self._exprs = exprs
        self._reduced_func = None

    def __str__(self):
        return '.'.join(x.to_str(is_method=True) for x in self._exprs)

    def __add__(self, other):
        assert isinstance(other, Query)
        return Query(*self._exprs, *other.exprs)

    @property
    def exprs(self):
        return self._exprs

    def then(self, call_expr):
        return Query(*self._exprs, call_expr)

    @typechecked
    def where(self, predicate: Callable):
        call_expr = call(where, parameter('self'), predicate)
        return self.then(call_expr)

    @typechecked
    def select(self, selector: Callable):
        call_expr = call(select, parameter('self'), selector)
        return self.then(call_expr)

    @typechecked
    def take(self, count: int):
        call_expr = call(take, parameter('self'), count)
        return self.then(call_expr)

    @typechecked
    def skip(self, count: int):
        call_expr = call(skip, parameter('self'), count)
        return self.then(call_expr)

    def to_memory(self):
        call_expr = call(to_memory, parameter('self'))
        return self.then(call_expr)

    def compile(self):
        '''
        compile the query as memory call.
        '''
        if self._reduced_func is None:
            if self.exprs:
                chain = []
                for expr in self.exprs:
                    assert expr.args and not expr.kwargs
                    args = [expr.value for expr in expr.args[1:]]
                    chain.append((expr.func, args))
                def func(src):
                    for fn, args in chain:
                        src = fn(src, *args)
                    return src
            else:
                def func(src):
                    return src
            self._reduced_func = func
        return self._reduced_func

EMPTY = Query()