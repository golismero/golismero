Plugin API
==========

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Plugin interfaces
-----------------

There is a general plugin interface. All sub classes implements and inherit their methods.

.. automodule:: golismero.api.plugin
   :members: Plugin, InformationPlugin, TestingPlugin, UIPlugin, ReportPlugin
   :show-inheritance:
   :inherited-members:

Data model
----------

.. toctree::

   data

Networking API
---------------

.. toctree::

   net

External tools API
------------------

.. automodule:: golismero.api.external
   :members: run_external_tool, win_to_cygwin_path, cygwin_to_win_path

Logging API
-----------

.. automodule:: golismero.api.logger
   :members: Logger
   :show-inheritance:
   :inherited-members:

Configuration API
-----------------

.. automodule:: golismero.api.config
   :members: Config, _Config
   :show-inheritance:
   :inherited-members:

Bundled files API
-----------------

.. automodule:: golismero.api.file
   :members:
   :show-inheritance:
   :inherited-members:

.. :autoclass:: golismero.api.file._FileManager
   :members:
   :show-inheritance:
   :inherited-members:

Parallel execution API
----------------------

.. automodule:: golismero.api.parallel
   :members: pmap, setInterval, TaskGroup, WorkerPool, Counter
   :show-inheritance:
   :inherited-members:

Shared data API
---------------

.. automodule:: golismero.api.shared
   :members: SharedMap, SharedHeap
   :show-inheritance:
   :inherited-members:

Audit database API
------------------

.. automodule:: golismero.api.data.db
   :members: Database
   :show-inheritance:
   :inherited-members:

Text processing API
-------------------

.. toctree::

   text

Audit control API
-----------------

.. automodule:: golismero.api.audit
   :members: get_audit_count, get_audit_names, get_audit_config, start_audit, stop_audit
