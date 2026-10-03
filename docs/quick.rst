Quick Start
===========

This page gets you started using JSONPath with Python. See :doc:`syntax` for an introduction to JSONPath expression syntax.

Find nodes
----------

:func:`jsonpath_rfc9535.find` applies a JSONPath expression to JSON-like data and returns a list of nodes - one instance of :class:`jsonpath_rfc9535.JSONPathNode` for each matched value.

A node contains both the matched value and its location in the argument data, plus methods for serializing locations to *normalized paths* and retrieving parent nodes.

.. code-block:: python

    import jsonpath_rfc9535 as jsonpath

    expr = "$.users[?@.status == 'pending'].name"

    data: dict[str, object] = {
        "users": [
            {"id": "usr_101", "name": "Alice", "status": "pending"},
            {"id": "usr_102", "name": "Bob", "status": "active"},
            {"id": "usr_103", "name": "Charlie", "status": "pending"},
        ],
    }

    for node in jsonpath.find(expr, data):
        print(node.path(), "->", node.value)

    # $['users'][0]['name'] -> Alice
    # $['users'][2]['name'] -> Charlie

``find()`` returns a :class:`list` subclass, :class:`jsonpath_rfc9535.JSONPathNodeList`, with methods for retrieving all values, locations or normalized paths for the entire list of nodes.

.. code-block:: python

   # ... continued from above

   nodes = jsonpath.find(expr, data)

   print(nodes.values())  # ['Alice', 'Charlie']
   print(nodes.locations())  # [('users', 0, 'name'), ('users', 2, 'name')]
   print(nodes.paths())  # ["$['users'][0]['name']", "$['users'][2]['name']"]

Find values
-----------

Use :func:`jsonpath_rfc9535.findall` instead of ``find()`` if you're interested in matched values only, without location and parent node information.

``findall()`` can be significantly faster and more memory efficient than ``find()``.

.. code-block:: python

    import jsonpath_rfc9535 as jsonpath

    expr = "$.users[?@.status == 'pending'].name"

    data: dict[str, object] = {
        "users": [
            {"id": "usr_101", "name": "Alice", "status": "pending"},
            {"id": "usr_102", "name": "Bob", "status": "active"},
            {"id": "usr_103", "name": "Charlie", "status": "pending"},
        ],
    }

    values = jsonpath.findall(expr, data)
    print(values)  # ['Alice', 'Charlie']


Node generator
--------------

:func:`jsonpath_rfc9535.finditer` yields instances of :class:`jsonpath_rfc9535.JSONPathNode` instead of materializing all nodes into a node list.

.. code-block:: python

    import jsonpath_rfc9535 as jsonpath

    expr = "$.users[?@.status == 'pending'].name"

    data: dict[str, object] = {
        "users": [
            {"id": "usr_101", "name": "Alice", "status": "pending"},
            {"id": "usr_102", "name": "Bob", "status": "active"},
            {"id": "usr_103", "name": "Charlie", "status": "pending"},
        ],
    }

    for node in jsonpath.finditer(expr, data):
        print(node.value)

Just the first node
-------------------

:func:`jsonpath_rfc9535.search` applies a JSONPath expression to JSON-like data and returns the first node found, or `None` if there were no matches.

.. code-block:: python

    import jsonpath_rfc9535 as jsonpath

    expr = "$.users[?@.status == 'pending'].name"

    data: dict[str, object] = {
        "users": [
            {"id": "usr_101", "name": "Alice", "status": "pending"},
            {"id": "usr_102", "name": "Bob", "status": "active"},
            {"id": "usr_103", "name": "Charlie", "status": "pending"},
        ],
    }

    node = jsonpath.search(expr, data)
    print(node.value)  # Alice

``search()`` is equivalent to:

.. code-block:: python

    # ... continued from above

    try:
        node = next(iter(jsonpath.finditer(expr, data)))
    except StopIteration:
        node = None

You could easily take, say, the first 5 nodes using :func:`~itertools.islice`.

.. code-block:: python

    # ... continued from above

    it = islice(jsonpath.finditer(expr, data), 5)


Compilation
-----------

Use :func:`jsonpath_rfc9535.compile` to parse a JSONPath expression for later evaluation, potentially against different data.

``compile()`` returns an instance of :class:`jsonpath_rfc9535.JSONPathQuery` with ``find()``, ``findall()``, ``finditer()`` and ``search()`` methods equivalent to the package level functions described above.

.. code-block:: python

    import jsonpath_rfc9535 as jsonpath

    query = jsonpath.compile("$.users[?@.status == 'pending'].name")

    data: dict[str, object] = {
        "users": [
            {"id": "usr_101", "name": "Alice", "status": "pending"},
            {"id": "usr_102", "name": "Bob", "status": "active"},
            {"id": "usr_103", "name": "Charlie", "status": "pending"},
        ],
    }

    nodes = query.find(data)
    # ...

We don't cache parsed queries between calls to ``find()``, ``finditer()``, etc. So it is well worth compiling your JSONPath expressions up front. 

Configuration
-------------

Package level functions ``find()``, ``findall()``, ``finditer()``, ``search()`` and ``compile()`` are convenience functions that use the default JSONPath environment. We can configure JSONPath by creating our own instance of :class:`jsonpath_rfc9535.JSONPathEnvironment` and using its ``find()``, ``findall()``, ``finditer()``, ``search()`` and ``compile()`` methods.

The arguments given in this example match the defaults.

.. code-block:: python

    from jsonpath_rfc9535 import JSONPathEnvironment, StandardParser

    env = JSONPathEnvironment(
        max_index=(2**53) - 1,
        min_index=-(2**53) + 1,
        max_recursion_depth=100,
        max_expression_depth=30,
        parser=StandardParser,
    )

    nodes = env.find("$.some.thing")
    # ...

An instance of ``JSONPathEnvironment`` is also where you'd register custom :doc:`functions`.

Exceptions
----------

``find()``, ``findall()``, ``finditer()``, ``search()`` and ``compile()`` functions and methods can raise exceptions at JSONPath expression compile time and/or query evaluation time.

All of the following exceptions inherit from :class:`jsonpath_rfc9535.JSONPathError`.

Compile time exceptions
^^^^^^^^^^^^^^^^^^^^^^^

* :code:`JSONPathSyntaxError`
* :code:`JSONPathNameError` (unknown filter function)
* :code:`JSONPathTypeError`
* :code:`JSONPathIndexError`
* :code:`JSONPathRecursionError` if a maximum expression depth is set.

Evaluation time exceptions
^^^^^^^^^^^^^^^^^^^^^^^^^^

* :code:`JSONPathRecursionError` if a descendant segment recursion limit is set.
* :code:`JSONPathError` when debugging regex filters.
