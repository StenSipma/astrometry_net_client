Concurrent Upload
=================

This example file covers the usage of the concurrent ``upload_files_gen``
method of the ``Client`` class. The key feature here is the way results are 
given back to the user; as a generator. This means that a result (as a job) is
given back whenever it is finished, which likely is not the order of which they
were uploaded.

Calling the script is similar to the :doc:`./client` example.

File can also be found at the source_

.. _source: https://github.com/StenSipma/astrometry_net_client/blob/master/examples/concurrent_upload.py
.. _client: client.rst

.. literalinclude:: ../../examples/concurrent_upload.py
   :language: python
