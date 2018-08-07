# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
import functools

ARGS_MAP_KINDS = (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)

def wrap_fast_fail(func):
    # resolve signature required args and kwargs nums
    # so we can fast crash on arguments not matchs.
    parameters = inspect.signature(func).parameters
    args_map = {} # {name: index}
    for index, parameter in enumerate(parameters.values()):
        if parameter.default is inspect.Parameter.empty:
            if parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
                args_map[parameter.name] = index
            elif parameter.kind is inspect.Parameter.KEYWORD_ONLY:
                args_map[parameter.name] = None

    def _(wraped_func):
        @functools.wraps(func)
        def fast_fail_func(*args, **kwargs):
            # for fast fail
            req_args = dict((k, args_map[k]) for k in args_map if k not in kwargs)
            if any(v is None for v in req_args.values()) or len(args) < len(req_args):
                return func(*args, **kwargs)
            return wraped_func(*args, **kwargs)
        return fast_fail_func
    return _
