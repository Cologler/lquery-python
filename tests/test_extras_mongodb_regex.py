# -*- coding: utf-8 -*-
#
# Copyright (c) 2018~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import re

from lquery.extras.mongodb import MongoDbQuery as QUERY_CLS

def test_regex():
    query = QUERY_CLS(None)
    query = query.where(lambda x: re.search('x{10}', x.name))
    assert query.query_options.filter == {'name': {'$regex': 'x{10}'}}
