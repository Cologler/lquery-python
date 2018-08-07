# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# a base extendable class
# ----------

import types

class Extendable:

    _ENTENSION_METHODS: dict = {}

    def __getattr__(self, attr):
        for kls in type(self).__mro__:
            ms = self._ENTENSION_METHODS.get(kls, {})
            func = ms.get(attr)
            if func is not None:
                return types.MethodType(func, self)
        raise AttributeError(f'{type(self)} has no attribute or extension method \'{attr}\'')

    @classmethod
    def _extend(cls, name, func):
        cls._ENTENSION_METHODS.setdefault(cls, {})[name] = func
        return func
