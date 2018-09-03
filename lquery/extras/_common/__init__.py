# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import asq.record

class NotSupportError(Exception):
    pass


class AlwaysEmptyError(Exception):
    def __init__(self, reason: str):
        self.reason = reason


class Record(asq.record.Record):
    def __getitem__(self, name):
        return vars(self)[name]


def new(**kwargs):
    return Record(**kwargs)
