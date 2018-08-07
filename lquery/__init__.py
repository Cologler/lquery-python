# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import Any

from .iterable import Iterable, IterableQuery

# pylint: disable=C0103
def enumerable(items: Iterable) -> Any:
    return IterableQuery(items)
