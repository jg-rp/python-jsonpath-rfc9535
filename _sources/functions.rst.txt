Function Extensions
===================

The JSONPath spec_ defines an extension point for functions that can be called from the :ref:`filter-selector`, and some standard function that all compliant JSONPath implementations must include.

Standard functions
------------------

count
^^^^^

.. code-block:: python

    count(nodes: NodeList) -> int

``count()`` returns the number of nodes in the argument node list. Usually ``count()`` will be given a filter query as its argument, and a call to ``count()`` must be part of a comparison expression.

.. code-block:: shell

    $.users[?count(@.*) > 2]

length
^^^^^^

.. code-block:: python

    length(value: object) -> int

``length()`` returns the length of the argument string or array, or the number of items in an object. A call to ``length()`` must be part of a comparison expression.

.. code-block:: shell

    $.users[?length(@) > 2]

match
^^^^^

.. code-block:: python

    match(value: str, pattern: str) -> bool

``match()`` returns ``true`` if `value` is a full match to the regular expression `pattern`, or ``false`` otherwise.

By default, ``false`` is returned if `pattern` is invalid.

.. code-block:: shell

    $.users[?match(@.name, '[Ss].*')]

search
^^^^^^

.. code-block:: python

    search(value: str, pattern: str) -> bool

``search`` returns ``true`` if `value` contains `pattern`, or ``false`` otherwise.

By default, ``false`` is returned if `pattern` is invalid.

.. code-block:: shell

    $.users[?search(@.name, '[Aa]')]

value
^^^^^

.. code-block:: python

    value(nodes: NodeList) -> object

``value()`` returns the value associated with the first node in `nodes` if `nodes` contains exactly one node. Usually, ``value()`` will be called with a filter query as its argument.

.. note::

    Filter queries that can result in at most one node are known as "singular queries", and all singular queries will be implicitly replaced with their value as required, without the use of ``value()``. ``value()`` is useful when you need the value from a query that can, theoretically, return multiple nodes.

Custom functions
----------------

Define a function extension by inheriting from :class:`jsonpath_rfc9535.FunctionExtension` and implementing its ``__call__()`` method.

The spec_ defines a type system for function expressions and rules for how those types can be used within the filter selector. Function extensions are required to declare their argument types and return type, and JSON P3 will raise a ``JSONPathTypeError`` at compile time if an expression is not deemed to be well-typed. See section 2.4.3 `Well-Typedness of Function Expressions`_.

In this example we implement a ``startswith()`` function that returns ``true`` if it's first argument is a string with a prefix matching the second argument.

.. code-block:: python

    from collections.abc import Sequence

    from jsonpath_rfc9535 import (
        LOGICAL_TYPE,
        VALUE_TYPE,
        ExpressionType,
        FunctionExtension,
        JSONPathEnvironment,
    )


    class StartsWith(FunctionExtension):
        arg_types: Sequence[ExpressionType] = (VALUE_TYPE, VALUE_TYPE)
        return_type: ExpressionType = LOGICAL_TYPE

        def __call__(self, value: object, prefix: object) -> bool:
            if not isinstance(value, str) or not isinstance(prefix, str):
                return False

            return value.startswith(prefix)

We then need to register an instance of ``StartsWith`` with a :class:`jsonpath_rfc9535.JSONPathEnvironment` by adding an entry to its ``functions`` dictionary.

.. code-block:: python

    # ... continued from above 

    env = JSONPathEnvironment()
    env.functions["startswith"] = StartsWith()

    query = env.compile("$.foo[?startswith(@.bar, 'baz')]")

You can replace or alias standard functions too, by adding entries to ``functions``.

.. _spec: https://datatracker.ietf.org/doc/html/rfc9535
.. _Well-Typedness of Function Expressions: https://datatracker.ietf.org/doc/html/rfc9535#name-well-typedness-of-function-
