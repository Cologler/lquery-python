# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# queryable for Iterable
# ----------

from typing import Union
from collections.abc import Iterable

from typeguard import typechecked

from .expr import CallExpr, ValueExpr, Make
from .queryable import AbstractQueryable, IQueryProvider, ReduceInfo
# load funcs for all extensions
from .funcs import _


class NextIterableQuery(AbstractQueryable):
    def __init__(self, expr):
        super().__init__(expr, PROVIDER)

    def __iter__(self):
        return iter(self.expr.resolve_value())

    def update_reduce_info(self, reduce_info):
        reduce_info.add_node(ReduceInfo.TYPE_MEMORY, self.expr)


class IterableQuery(NextIterableQuery):
    @typechecked
    def __init__(self, items: Iterable):
        super().__init__(Make.ref(items))

    def __str__(self):
        return f'IQueryable({self.expr.value})'

    def update_reduce_info(self, reduce_info):
        reduce_info.add_node(ReduceInfo.TYPE_SRC, self.expr)


class IterableQueryProvider(IQueryProvider):
    def create_query(self, expr: CallExpr):
        return NextIterableQuery(expr)

    def execute(self, expr: Union[ValueExpr, CallExpr]):
        return expr.resolve_value()

PROVIDER = IterableQueryProvider()
