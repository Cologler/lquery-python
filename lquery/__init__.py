# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .iterable import IterableQuery, Queryable

def enumerable(src) -> Queryable:
    return IterableQuery(src)
