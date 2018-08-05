# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from .._common import NotSupportError, AlwaysEmptyError

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

    def op_not(self):
        raise NotSupportError

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

    @staticmethod
    def filter_field_exists(field_name):
        updater = QueryOptionsFilterFieldExistsUpdater(field_name)
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

    def _try_merge(self, exists, value):
        if exists == value:
            return value
        if isinstance(exists, dict) and isinstance(value, dict):
            merged_value = dict(exists)
            if all(k.startswith('$') for k in exists) and all(k.startswith('$') for k in value):
                for k in value:
                    v = value[k]
                    if k in merged_value:
                        ev = merged_value[k]
                        if k == '$gt':
                            merged_value[k] = max(ev, v)
                        elif k == '$lt':
                            merged_value[k] = min(ev, v)
                    else:
                        # reduce
                        if k == '$gt':
                            if '$lt' in merged_value:
                                ev = merged_value['$lt']
                                if ev <= v:
                                    raise AlwaysEmptyError(f'{v} < $value < {ev}')
                        elif k == '$lt':
                            if '$gt' in merged_value:
                                ev = merged_value['$gt']
                                if ev >= v:
                                    raise AlwaysEmptyError(f'{ev} < $value < {v}')
                        merged_value[k] = v
            return merged_value
        raise NotSupportError

    def add_pairs(self, field_name, value):
        if field_name in self.data:
            self.data[field_name] = self._try_merge(self.data[field_name], value)
        else:
            self.data[field_name] = value

    def apply(self, options: QueryOptions):
        for name, value in self.data.items():
            if name in options.filter:
                exists = options.filter[name]
                options.filter[name] = self._try_merge(exists, value)
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


class QueryOptionsFilterFieldExistsUpdater(QueryOptionsUpdater):
    def __init__(self, field_name, value: bool=True):
        self._field_name = field_name
        self._value = value

    def op_not(self):
        return QueryOptionsFilterFieldExistsUpdater(self._field_name, not self._value)

    def apply(self, options: QueryOptions):
        data = options.filter.get(self._field_name, None)
        if data is None:
            options.filter[self._field_name] = {'$exists': self._value}
        else:
            raise NotSupportError
