# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from abc import abstractmethod
from collections.abc import Iterable
from functools import wraps

from .extendable import Extendable


class IEnumerable(Extendable):

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError('you should implement the query in subclass.')

    @classmethod
    def extend_linq(cls, return_queryable: bool, name: str = None):
        '''
        allow user add extension methods for `IEnumerable`.
        '''
        def _(func):
            method_name = name or func.__name__
            @wraps(func)
            def wraped_func(self, *args, **kwargs):
                ret = func(self, *args, **kwargs)
                return Enumerable(ret) if return_queryable else ret
            cls._extend(method_name, wraped_func)
            return func
        return _


class Enumerable(IEnumerable):
    def __init__(self, items: Iterable):
        super().__init__()
        self._items = items

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, k):
        try:
            return self._items[k]
        except KeyError: # raise on dict.
            raise TypeError
