# lquery

try bring C# linq to python.

this library is a demo, not for production (yet).

## COMPARE

For C#:

``` cs
IQueryable<?> query = null;
var items = query.Where(z => z.Name == 's').Select(z => z.Value).ToList();
```

So for python:

``` py
query: Queryable = None;
expr = query.where(z => z.name == 's').select(z => z.value).to_list();
```

## for in-memory iterable

``` py
from lquery import enumerable
query: Queryable = enumerable([1, 2, 3])
# then query it
```

## for mongodb

``` py
from lquery.extras.mongodb import MongoDbQuery
collection = # get a collection from pymongo
query: Queryable = MongoDbQuery(collection)
# then query it
```

## linq APIs

* where
* select
* take
* skip

read more from `test.py`.
