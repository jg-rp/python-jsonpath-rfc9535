JSONPath Syntax
===============

This page provides a short introduction to `RFC 9535`_ JSONPath syntax.


Terminology
-----------

Think of a JSON document as a tree, objects and arrays can contain other objects, arrays, or scalar values. Each of these (object, array, or scalar) is a **node** in the tree. The outermost object or array is called the **root** node.

A JSONPath expression (aka "query") is made up of a sequence of **segments**. Each segment contains one or more **selectors**:

* A *segment* corresponds to a step in the path from one set of nodes to the next.
* A *selector* describes how to choose nodes within that step (for example, by name, by index, or by wildcard).

Root identifier
---------------

The root identifier, ``$``, refers to the outermost node in the target document. This can be an object, an array, or a scalar value.

A query containing only the root identifier simply returns the entire input document.

.. code-block:: shell
    :caption: query
    
    $

.. code-block:: javascript
    :caption: data
    
    {
      "categories": [
        { "id": 1, "name": "fiction" },
        { "id": 2, "name": "non-fiction" }
      ]
    }

.. code-block:: javascript
    :caption: results

    [
      {
        "categories": [
          { "id": 1, "name": "fiction" },
          { "id": 2, "name": "non-fiction" }
        ]
      }
    ]

Selectors
---------

Name selector
^^^^^^^^^^^^^

The *name selector* matches the value of an object member by its key. You can write it in either **shorthand notation** (``.thing``) or **bracket notation** (``['thing']`` or ``["thing"]``).

Dot notation can be used when the property name is a valid identifier. Bracket notation is required when the property name contains spaces, special characters, or starts with a number.

.. code-block:: shell
    :caption: query
    
    $.book.title

.. code-block:: javascript
    :caption: data
    
    {
      "book": {
        "title": "Moby Dick",
        "author": "Herman Melville"
      }
    }

.. code-block:: javascript
    :caption: results

    ["Moby Dick"]

If a JSON object key contains a dot (``.``), space or other reserved symbol, use bracket notation instead of shorthand dot notation to select it.

.. code-block:: shell
    :caption: query
    
    $["book.title"]

.. code-block:: javascript
    :caption: data
    
    {
      "book.title": "Moby Dick",
      "book.author": "Herman Melville"
    }

.. code-block:: javascript
    :caption: results

    ["Moby Dick"]


When using bracket notation, names can be surrounded by single or double quotes. These two queries are equivalent.

.. code-block:: shell

    $["book.title"]
    $['book.title']


Index selector
^^^^^^^^^^^^^^

The index selector selects an element from an array by its index. Indices are zero-based and enclosed in brackets, ``[0]``. If the index is negative, items are selected from the end of the array.

.. code-block:: shell
    :caption: query
    
    $.categories[0].name

.. code-block:: javascript
    :caption: data
    
    {
      "categories": [
        { "id": 1, "name": "fiction" },
        { "id": 2, "name": "non-fiction" }
      ]
    }

.. code-block:: javascript
    :caption: results

    ["fiction"]

Wildcard selector
^^^^^^^^^^^^^^^^^

The *wildcard selector* matches all member values of an object or all elements in an array. It can be written as ``.*`` (shorthand notation) or ``[*]`` (bracket notation).

.. code-block:: shell
    :caption: query
    
    $.categories[*].name

.. code-block:: javascript
    :caption: data
    
    {
      "categories": [
        { "id": 1, "name": "fiction" },
        { "id": 2, "name": "non-fiction" }
      ]
    }

.. code-block:: javascript
    :caption: results

    ["fiction", "non-fiction"]

Slice selector
^^^^^^^^^^^^^^

The slice selector allows you to select a range of elements from an array. A start index, ending index and step size are all optional and separated by colons, ``[start:end:step]``. Negative indices count from the end of the array.

.. code-block:: shell
    :caption: query
    
    $.items[1:4:2]

.. code-block:: javascript
    :caption: data
    
    {
      "items": ["a", "b", "c", "d", "e", "f"]
    }

.. code-block:: javascript
    :caption: results

    ["b", "d"]

.. _filter-selector:

Filter selector
^^^^^^^^^^^^^^^

The filter selector allows you to select nodes using a Boolean expression, ``[?expression]``, with conventional comparison operators (``==``, ``!=``, ``<``, ``>``, ``<=``, and ``>=```), logical operators (``&&`` and ``||``), and parentheses for grouping terms.

A *filter query* is a nested JSONPath expression starting with either the root identifier (``$``), meaning the query is evaluated relative to the document root, or the *current node identifier*, meaning the query is evaluated relative to the current node.

When filtering an object, ``@`` identifies the current member value. When filtering an array, ``@`` identifies the current element.

A filter query on its own, without a comparison, is treated as an existence test.

.. code-block:: shell
    :caption: query
    
    $..products[?(@.price < $.price_cap)]

.. code-block:: javascript
    :caption: data
    
    {
      "price_cap": 10,
      "products": [
        { "name": "apple", "price": 5 },
        { "name": "orange", "price": 12 },
        { "name": "banana", "price": 8 }
      ]
    }

.. code-block:: javascript
    :caption: results

    [
      { "name": "apple", "price": 5 },
      { "name": "banana", "price": 8 }
    ]

Segments
--------

So far we've seen shorthand notation (``.selector``) and bracket notation with just one selector (``[selector]``). Here we cover the descendant segment and segments with multiple selectors.

Multiple selectors
^^^^^^^^^^^^^^^^^^

A segment can include multiple selectors separated by commas and enclosed in square brackets (``[selector, selector, ...]``). Any valid selector (name, index, slice, filter, or wildcard) can appear in the list.

.. code-block:: shell
    :caption: query
    
    $.store.book[0,2]

.. code-block:: javascript
    :caption: data
    
    {
      "store": {
        "book": [
          { "title": "Book A", "price": 10 },
          { "title": "Book B", "price": 12 },
          { "title": "Book C", "price": 8 }
        ]
      }
    }

.. code-block:: javascript
    :caption: results

    [
      { "title": "Book A", "price": 10 },
      { "title": "Book C", "price": 8 }
    ]

Descendant segments
^^^^^^^^^^^^^^^^^^^

The descendant segment (``..``) visits all object member values and array elements under the current object or array, applying the selector or selectors that follow to each visited node. It must be followed by a shorthand selector (name, wildcard, etc.) or a bracketed list of one or more selectors.


.. code-block:: shell
    :caption: query
    
    $..price

.. code-block:: javascript
    :caption: data
    
    {
      "store": {
        "book": [
          { "title": "Book A", "price": 10 },
          { "title": "Book B", "price": 12 }
        ],
        "bicycle": { "color": "red", "price": 19.95 }
      }
    }

.. code-block:: javascript
    :caption: results

    [10, 12, 19.95]

.. _RFC 9535: https://datatracker.ietf.org/doc/html/rfc9535
.. _JSONPath Compliance Test Suite: https://github.com/jsonpath-standard/jsonpath-compliance-test-suite