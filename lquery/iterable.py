# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# queryable for Iterable
# ----------

from collections import Iterable

from typeguard import typechecked

from .queryable import Queryable, QueryProvider

class IterableQuery(Queryable):
    @typechecked
    def __init__(self, items: Iterable):
        super().__init__(None, PROVIDER)
        self._items = items

    def __iter__(self):
        return iter(self._items)

    def __str__(self):
        return f'Queryable({str(self._items)})'


class IterableQueryProvider(QueryProvider):

    def create_query(self, src, query):
        return IterableQuery(src).update_query(query)

    def execute(self, queryable: Queryable):
        if queryable.src is None:
            yield from queryable
        else:
            yield from self._execute_in_memory(queryable)

PROVIDER = IterableQueryProvider()
