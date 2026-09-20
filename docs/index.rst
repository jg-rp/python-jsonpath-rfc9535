Query Expressions for JSON in Python
====================================

JSONPath is a query language for selecting values from `JSON`_-like data. A
JSONPath query has the potential to return multiple values from a data
structure, along with their locations.

This implementation is non-evaluating and read-only. We follow `RFC 9535`_
and test against the `JSONPath Compliance Test Suite`_.

.. note::

   We use the term "JSON-like data" to describe arbitrary Python lists,
   dictionaries, strings, numbers, Booleans and ``None``, as you would get from
   ``json.load()``. When traversing dictionaries we ignore non-string keys.

   See `python-jsonpath`_ if you need to query any :class:`~collections.abc.Sequence`
   or :class:`~collections.abc.Mapping` instead of just lists and dictionaries.

Install
-------

Install ``jsonpath-rfc9535`` from PyPI_ using your favorite package manager.

**pip**

.. code-block:: shell

   python -m pip install jsonpath-rfc9535

**uv**

.. code-block:: shell

   uv add jsonpath-rfc9535   

**pipenv**

.. code-block:: shell

   pipenv install -u jsonpath-rfc9535

Examples
--------

.. code-block:: python

   import jsonpath_rfc9535 as jsonpath

   data = {
      "users": [
         {"name": "Sue", "score": 100},
         {"name": "Sally", "score": 84, "admin": False},
         {"name": "John", "score": 86, "admin": True},
         {"name": "Jane", "score": 55},
      ],
      "moderator": "John",
   }

   for node in jsonpath.find("$.users[?@.score > 85]", data):
      print(node.value)

   # {'name': 'Sue', 'score': 100}
   # {'name': 'John', 'score': 86, 'admin': True}

Or read data from a file:

.. code-block:: python

   import json
   import jsonpath_rfc9535 as jsonpath

   with open("path/to/some.json", encoding="utf-8") as fd:
      data = json.load(fd)

   nodes = jsonpath.find("$.some.query", data)
   values = nodes.values()
   # ...

You can query data from a YAML formatted file too, or any format that can be
loaded into dictionaries and lists. If you have `PyYAML`_ installed:

.. code-block:: python

   import jsonpath_rfc9535 as jsonpath
   import yaml

   with open("some.yaml") as fd:
      data = yaml.safe_load(fd)

   values = jsonpath.find("$..products.*", data).values()
   # ...

.. _JSON: https://www.json.org/json-en.html
.. _RFC 9535: https://datatracker.ietf.org/doc/html/rfc9535
.. _JSONPath Compliance Test Suite: https://github.com/jsonpath-standard/jsonpath-compliance-test-suite
.. _PyPI: https://pypi.org/project/jsonpath-rfc9535
.. _python-jsonpath: https://github.com/jg-rp/python-jsonpath
.. _PyYAML: https://pyyaml.org/wiki/PyYAML

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   syntax.rst
   functions.rst
   api.rst