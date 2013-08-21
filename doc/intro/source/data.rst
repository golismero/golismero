Data API
========

The GoLismero data model is divided into three fundamental types of data:
 - Information
 - Resource
 - Vulnerability

Common properties to all data types
-----------------------------------

All data types in the GoLismero data model have a common interface:

.. automodule:: golismero.api.data
   :members: Data
   :special-members:

The Information interface
-------------------------

This is the common interface for informational data:

.. automodule:: golismero.api.data.information
   :members:
   :show-inheritance:
   :special-members:

The Resource interface
----------------------

This is the common interface for resouce location data:

.. automodule:: golismero.api.data.resource
   :members:
   :show-inheritance:
   :special-members:

The Vulnerability interface
---------------------------

This is the common interface for vulnerabilities found by GoLismero plugins:

.. automodule:: golismero.api.data.vulnerability
   :members:
   :show-inheritance:
   :special-members:
   :noindex:

Concrete data types
-------------------

Here you can find all concrete data types available in the GoLismero data model:

.. toctree::

   Information<data.information>
   Resource<data.resource>
   Vulnerability<data.vulnerability>
