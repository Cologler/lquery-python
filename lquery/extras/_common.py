# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

class NotSupportError(Exception):
    pass


class AlwaysEmptyError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
