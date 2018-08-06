# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
# the common predicate for databases
# ----------

'''
all operators:

# unary
not,

# binary
==, >, >=, <, <=,
'''

from operator import attrgetter

from ._common import NotSupportError, AlwaysEmptyError


class Predicate:
    def can_merge(self, other) -> bool:
        '''
        test whether can merge two predicate.
        '''
        return False

    def merge(self, other):
        '''
        merge two predicate.
        '''
        raise NotSupportError

    @classmethod
    def binary(cls, op, value):
        return BinaryPredicate(op, value)


class BinaryPredicate(Predicate):
    def __init__(self, op, value):
        self._op = op
        self._value = value

    def __str__(self):
        return f'{self.op} {self.value}'

    def __eq__(self, other):
        if isinstance(other, BinaryPredicate):
            return (self.op, self.value) == (other.op, other.value)
        return False

    @property
    def op(self):
        return self._op

    @property
    def value(self):
        return self._value

    def can_merge(self, other):
        if isinstance(other, BinaryPredicate):
            if self._op == other.op:
                return self._op in self._TABLE_MERGE_SAME_OP
            else:
                oops = [tuple([self._op, other.op]), tuple([other.op, self._op])]
                return any(oop in self._TABLE_MERGE_DIFF_OP for oop in oops)
        return super().can_merge(other)

    def merge(self, other):
        if isinstance(other, BinaryPredicate):
            if self._op == other.op:
                return self._TABLE_MERGE_SAME_OP[self._op](self, other)
            else:
                opps = [tuple([self._op, other.op]), tuple([other.op, self._op])]
                for opp in opps:
                    func = self._TABLE_MERGE_DIFF_OP.get(opp)
                    if func is not None:
                        if opp[0] == self._op:
                            return func(self, other)
                        else:
                            return func(other, self)
        return super().merge(other)

    _TABLE_MERGE_SAME_OP = {}

    @classmethod
    def cb_merge_same_op(cls, *ops):
        def _(func):
            for op in ops:
                cls._TABLE_MERGE_SAME_OP[op] = func
            return func
        return _

    _TABLE_MERGE_DIFF_OP = {}

    @classmethod
    def cb_merge_diff_op(cls, *opps):
        def _(func):
            for opp in opps:
                # opp is op pair like ('==', '>')
                cls._TABLE_MERGE_DIFF_OP[opp] = func
            return func
        return _


@BinaryPredicate.cb_merge_same_op('==')
def same_op_merge_eq(self, other):
    if self.value != other.value:
        raise AlwaysEmptyError(f'cannot equals both value: ({self.value}, {other})')
    return self

@BinaryPredicate.cb_merge_same_op('>', '>=')
def same_op_merge_g(self, other):
    # take max
    return max(self, other, key=attrgetter('value'))

@BinaryPredicate.cb_merge_same_op('<', '<=')
def same_op_merge_l(self, other):
    # take min
    return min(self, other, key=attrgetter('value'))

@BinaryPredicate.cb_merge_diff_op(('==', '>'))
def diff_op_merge_eq_gt(first, second):
    if first.value <= second.value:
        raise AlwaysEmptyError(f'cannot ($ == {first.value}) and ($ {second.op} {second.value})')
    return first

@BinaryPredicate.cb_merge_diff_op(('==', '>='))
def diff_op_merge_eq_ge(first, second):
    if first.value < second.value:
        raise AlwaysEmptyError(f'cannot ($ == {first.value}) and ($ {second.op} {second.value})')
    return first

@BinaryPredicate.cb_merge_diff_op(('>=', '>'))
def diff_op_merge_g(first, second):
    # take max
    if first.value == second.value:
        return second
    return max(first, second, key=attrgetter('value'))

@BinaryPredicate.cb_merge_diff_op(('<', '<='))
def diff_op_merge_l(first, second):
    # take min
    if first.value == second.value:
        return first
    return min(first, second, key=attrgetter('value'))
