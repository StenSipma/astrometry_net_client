*********************
Astrometry.net Client
*********************

.. image:: https://readthedocs.org/projects/astrometry-net-client/badge/?version=latest
   :target: https://astrometry-net-client.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
   
.. image:: https://github.com/StenSipma/astrometry_net_client/workflows/Build%20&%20Tests/badge.svg
   :target: https://github.com/StenSipma/astrometry_net_client/actions?query=workflow%3A%22Build+%26+Tests%22
   :alt: Build & Tests Status

.. note:: 
   The package is still in development, but it can already be used. 
   Do not hesitate to leave any feedback (positive or negative)!

Quickstart
----------

Install the package via pip:

.. code:: bash

        pip install astrometry-net-client

Get your API key from: `api_help`_, and paste it in a plaintext file (name it something like `key`).

A script called `anc_upload` should be included with the install.

.. _api_help: https://nova.astrometry.net/api_help



Introduction
------------

This package is meant to be a simple but extensible interface for the `Astrometry.net API`_.
A higher level interface is offered through the ``Client`` class, combining most functionality.
However, if you want more control over the requests (e.g. by manually checking the responses), you can also use the ``Job``, ``Submission`` and ``UploadFile`` classes directly.

The structure of these classes tries to follow the pattern of the API itself, which is essentially:

1. Upload some file (``UploadFile``), which requires an API key & a login (``Session``)
2. The upload creates a submission (``Submission``), unique for each upload. This has to do some general processing, even before the uploaded image is processed.
3. When the submission is done preprocessing, and the system is ready to process the uploaded file, a job (``Job``) is spawned for each image.
4. The job then takes some time to process, and when it is done it can either be successful or fail.
5. When successful, some information (e.g. found objects) and result files like the generated WCS header can be retrieved.

Using this package, these steps are (note that this is not the ideal way to upload multiple files):

.. code:: python
   
    from astrometry_net_client import Session
    from astrometry_net_client import FileUpload

    s = Session(api_key='xxxxxxxxx')
    upl = FileUpload('some/file/name', session=s) # 1.
    submission = upl.submit()                     # 2.
    submission.until_done()                       # blocks until it is finished       
    job = submission.jobs[0]                      # 3.
    job.until_done()                              # 4. (again blocks)
    if job.success():
        wcs = job.wcs_file()                      # 5. (only if successful)
    print(job.info())                             # works even though the job failed

Or with the higher level ``Client`` :

.. code:: python
   
    from astrometry_net_client import Client

    c = Client(api_key='xxxxxxxxxx')

    # WARNING: this can take a while, as it blocks until the file is solved.
    # wcs will be None if upload is not successful
    wcs = c.calibrate_file_wcs(filename)  

One of the core ideas of this package is to try and make the minimal amount of requests possible and make them at a clear time. This is realized by the following *initialize & send* pattern:

.. code:: python

    r = Request(url)    # initialize (request not yet sent)
    response = r.make() # send the request

Similarely, retrieving files like the WCS file (after a successful ``Job``) will be done once and cached thereafter:

.. code:: python

    wcs = job.wcs_file()    # first call makes the actual request
    wcs_2 = job.wcs_file()  # second call uses previously obtained result

.. _Astrometry.net API: http://nova.astrometry.net/


Installation
------------

Installation required python version 3.8 or greater.

Simpy install the package usng PyPi:

.. code:: bash

        pip install astrometry-net-client

Note that the development and testing of this package is done on Linux, so it
may not work on a different platform.

Installing From Source
""""""""""""""""""""""

Installing the package from source is made easy by the Makefile, once you have a local copy of the repository (e.g. by cloning, or downloading & extracting the repo ZIP).

It is heavily recommended to use a virtual environment. Create and activate one by running:

.. code:: bash

        make virt-env
        source .env/bin/activate
        pip install wheel

Then build & install the package with (does not install development dependencies):

.. code:: bash

        make install

Documentation
-------------
Documentation is available at `Readthedocs`_

.. _Readthedocs: https://astrometry-net-client.readthedocs.io/en/latest/

There is a local documentation available (defined by docstrings). To access it, first  install the package and the development dependencies:

.. code:: bash

        make dependencies
        
then generate the documentation (using Sphinx) by:

.. code:: bash

        make documentation

The main page can then be found at (assuming you are in the project root) ``./docs/_build/html/index.html``. Open this (for example) with:

.. code:: bash

        firefox ./docs/_build/html/index.html

Examples
--------
Some example files/scripts are found at the `examples entry`_ of the documentation.

Some elaborate examples can be found in the ``examples`` directory. 
For more specific usage, refer to the `documentation`_.

.. _examples entry: https://astrometry-net-client.readthedocs.io/en/latest/examples/overview.html
.. _documentation: https://astrometry-net-client.readthedocs.io/en/latest
