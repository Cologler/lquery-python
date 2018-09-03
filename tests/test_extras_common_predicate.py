# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import pytest
from pytest import raises

from lquery.extras._common.predicate import Predicate, BinaryPredicate, PredicateConflictError

def unpack(predicate: Predicate):
    if isinstance(predicate, BinaryPredicate):
        return predicate.op, predicate.value
    raise NotImplementedError

def merge(first: Predicate, second: Predicate):
    assert first.merge(second) == second.merge(first)
    return first.merge(second)

def test_binary():
    assert Predicate.create_binary('==', 15) == Predicate.create_binary('==', 15)
    assert Predicate.create_binary('==', 15) != Predicate.create_binary('==', 14)

def test_binary_equal():
    assert Predicate.create_binary('==', 15) == Predicate.create_binary('==', 15)
    assert Predicate.create_binary('==', 15) != Predicate.create_binary('==', 14)
    assert Predicate.create_binary('==', 15) != Predicate.create_binary('>', 15)

def test_binary_merge():
    eq_15 = Predicate.create_binary('==', 15)

    assert eq_15.can_merge(eq_15)
    assert eq_15.merge(eq_15) is eq_15
    assert eq_15.merge(Predicate.create_binary('==', 15)) is eq_15

def test_binary_merge_conflict():
    eq_3 = Predicate.create_binary('==', 3)

    with raises(PredicateConflictError):
        eq_3.merge(Predicate.create_binary('>', 4))

    with raises(PredicateConflictError):
        eq_3.merge(Predicate.create_binary('>=', 4))

    with raises(PredicateConflictError):
        eq_3.merge(Predicate.create_binary('>', 3))

    assert merge(eq_3, Predicate.create_binary('>=', 3)) is eq_3
    assert merge(eq_3, Predicate.create_binary('>', 2)) is eq_3
    assert merge(eq_3, Predicate.create_binary('>=', 2)) is eq_3
