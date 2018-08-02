# lquery

Try bring C# linq to python 🎈.

The library is a demo, not for production (yet).

## Compare with Others

Different between lquery and others (linq for python like asq):

**lquery try convert func (from bytecode) to SQL and query from database process.**

## Compare with CSharp

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

### for in-memory iterable

``` py
from lquery import enumerable
query: Queryable = enumerable([1, 2, 3])
# then query it
```

### for mongodb

``` py
from lquery.extras.mongodb import MongoDbQuery
collection = # get a collection from pymongo
query: Queryable = MongoDbQuery(collection)
# then query it
```

## linq APIs

* `to_memory` - same as `AsEnumerable()` from C#
* `where`
* `select`
* `select_many`
* `take`
* `skip`

read more examples from unittests.

## Others

### print reduce info

Print reduce info is easy way to check what query will compile to SQL.

code example:

``` py
>>> from lquery.extras.mongodb import MongoDbQuery
>>> mongo_query = MongoDbQuery(None)
>>> reduce_info = mongo_query\
...     .where(lambda x: (x['size']['h'] == 14) & (x['size']['uom'] == 'cm'))\
...     .skip(1)\
...     .where(lambda x: x['size']['w'] > 15)\
...     .get_reduce_info()
>>> reduce_info.print()
reduce info of:
  Queryable()
    .where(<function <lambda> at 0x0000025DBC661EA0>)
    .skip(1)
    .where(<function <lambda> at 0x0000025DBE957840>)
=>
    [SQL] where(<function <lambda> at 0x0000025DBC661EA0>)
    [SQL] skip(1)
    [MEM] where(<function <lambda> at 0x0000025DBE957840>)
```

you can see the 1st `where()` and 1st `skip()` was success compile to SQL, and 2nd `where()` only work inside python process.
