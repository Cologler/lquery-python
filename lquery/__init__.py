# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from collections.abc import Iterable
from typing import Any

from .enumerable import Enumerable

# pylint: disable=C0103
def enumerable(items: Iterable) -> Any:
    return Enumerable(items)
