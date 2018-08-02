# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .._common import NotSupportError

class QueryOptions:
    def __init__(self):
        self.filter = {}
        self.skip = None
        self.limit = None

    def get_cursor(self, collection):
        cursor = collection.find(
            filter=self.filter,
            skip=self.skip or 0,
            limit=self.limit or 0)
        return cursor


class QueryOptionsUpdater:
    def apply(self, options: QueryOptions):
        raise NotImplementedError

    @staticmethod
    def add_skip(value):
        return QueryOptionsSkipUpdater(value)

    @staticmethod
    def add_limit(value):
        return QueryOptionsLimitUpdater(value)

    @staticmethod
    def add_filter_field(field_name, value):
        updater = QueryOptionsFilterFieldUpdater()
        updater.add_pairs(field_name, value)
        return updater


class QueryOptionsSkipUpdater(QueryOptionsUpdater):
    def __init__(self, value):
        self._value = value

    def apply(self, options: QueryOptions):
        if options.skip is None:
            options.skip = self._value
        else:
            options.skip += self._value


class QueryOptionsLimitUpdater(QueryOptionsUpdater):
    def __init__(self, value):
        self._value = value

    def apply(self, options: QueryOptions):
        if options.limit is None:
            options.limit = self._value
        else:
            options.limit = min(options.limit, self._value)


class QueryOptionsFilterFieldUpdater(QueryOptionsUpdater):
    def __init__(self):
        self.data = {}

    def add_pairs(self, field_name, value):
        if field_name in self.data:
            raise NotSupportError
        self.data[field_name] = value

    def apply(self, options: QueryOptions):
        for name, value in self.data.items():
            if options.filter.get(name, value) != value:
                raise NotSupportError
            else:
                options.filter[name] = value

    def __and__(self, other):
        assert isinstance(other, QueryOptionsFilterFieldUpdater)
        new_updater = QueryOptionsFilterFieldUpdater()
        for name, value in self.data.items():
            new_updater.add_pairs(name, value)
        for name, value in other.data.items():
            new_updater.add_pairs(name, value)
        return new_updater
