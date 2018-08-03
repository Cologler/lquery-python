# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# lquery for tinydb
# ----------

from ..iterable import IterableQuery

class TinyDbQuery(IterableQuery):
    def __init__(self, table):
        super().__init__(table)

