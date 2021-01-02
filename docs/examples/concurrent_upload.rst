Concurrent Upload
=================

This example file covers the usage of the concurrent ``upload_files_gen``
method of the ``Client`` class. The key feature here is the way results are
given back to the user; as a generator. This means that a result (as a job) is
given back whenever it is finished, which likely is not the order of which they
were uploaded.

Calling the script is similar to the :doc:`./client` example.

The files which are uploaded are restricted to FITS files, but this is not the
case in general. If you want to make this example work for any file type
(accepted by Astrometry.net), remove the usage of the ``enough_sources`` filter
function, and then also remove the line containing ``filter(is_fits, ...)``. If
you do this, you should be more careful not to include invalid files (or
directories) when running the script.

An additional dependency of ``photutils`` is required in order to run this
script: ``pip install photutils``. This is used in the ``enough_sources``
function.

File can also be found at the source_

.. _source: https://github.com/StenSipma/astrometry_net_client/blob/master/examples/concurrent_upload.py
.. _client: client.rst

.. literalinclude:: ../../examples/concurrent_upload.py
   :language: python
