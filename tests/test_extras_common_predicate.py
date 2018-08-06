# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import pytest

from lquery.extras._common import AlwaysEmptyError
from lquery.extras._common_predicate import Predicate, BinaryPredicate

def to_tuple(predicate: BinaryPredicate):
    return predicate.op, predicate.value

def test_binary():
    assert to_tuple(Predicate.binary('==', 15)) == ('==', 15)
    assert Predicate.binary('==', 15) == Predicate.binary('==', 15)
    assert Predicate.binary('==', 15) != Predicate.binary('==', 14)

def test_binary_eq():
    assert Predicate.binary('==', 15).can_merge(Predicate.binary('==', 15))
    assert Predicate.binary('==', 15).merge(Predicate.binary('==', 15)) == Predicate.binary('==', 15)
    with pytest.raises(AlwaysEmptyError):
        Predicate.binary('==', 15).merge(Predicate.binary('==', 14))

def test_binary_eq_conflict():
    with pytest.raises(AlwaysEmptyError):
        Predicate.binary('==', 3).merge(Predicate.binary('>', 4))

    with pytest.raises(AlwaysEmptyError):
        Predicate.binary('==', 3).merge(Predicate.binary('>=', 4))

    with pytest.raises(AlwaysEmptyError):
        Predicate.binary('==', 3).merge(Predicate.binary('>', 3))

    assert Predicate.binary('==', 3).merge(Predicate.binary('>=', 3)) == Predicate.binary('==', 3)

    assert Predicate.binary('==', 3).merge(Predicate.binary('>', 2)) == Predicate.binary('==', 3)

    assert Predicate.binary('==', 3).merge(Predicate.binary('>=', 2)) == Predicate.binary('==', 3)
