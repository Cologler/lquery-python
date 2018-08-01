
lquery
======

Try bring C# linq to python 🎈.

The library is a demo, not for production (yet).

Compare with Others
-------------------

Different between lquery and others (linq for python like asq):

**lquery try convert func (from bytecode) to SQL and query from database process.**

Compare with CSharp
-------------------

For C#:

.. code-block:: cs

   IQueryable<?> query = null;
   var items = query.Where(z => z.Name == 's').Select(z => z.Value).ToList();

So for python:

.. code-block:: py

   query: Queryable = None;
   expr = query.where(z => z.name == 's').select(z => z.value).to_list();

for in-memory iterable
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: py

   from lquery import enumerable
   query: Queryable = enumerable([1, 2, 3])
   # then query it

for mongodb
^^^^^^^^^^^

.. code-block:: py

   from lquery.extras.mongodb import MongoDbQuery
   collection = # get a collection from pymongo
   query: Queryable = MongoDbQuery(collection)
   # then query it

linq APIs
---------


* ``to_memory`` - same as ``AsEnumerable()`` from C#
* ``where``
* ``select``
* ``select_many``
* ``take``
* ``skip``

read more examples from unittests.
