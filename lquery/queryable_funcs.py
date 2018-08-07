# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import abc
from typing import Any

from .queryable import IQueryable
from .enumerable import Enumerable

class Queryable:

    @abc.abstractmethod
    def __iter__(self):
        # added this method so linter will not show error.
        raise NotImplementedError

    @IQueryable.extend_linq(False)
    def load(self) -> Any:
        '''
        force load data into memory.
        '''
        return Enumerable(self)

# for load from outside:
_ = None
