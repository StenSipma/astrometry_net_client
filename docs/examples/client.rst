Client
======

This example covers the basic use of the Client class, where it is used to
upload a given list of files and save the successful calibrations. 
It is executed as follows::
        
        $ python3 client.py path/to/keyfile file.fits another.fits directory/*.fits

where the first argument is the location of the api key and the remaining
arguments are (paths to) fits files.

GitHub source is found here_.

.. _here: https://github.com/StenSipma/astrometry_net_client/blob/master/examples/client.py

.. literalinclude:: ../../examples/client.py
   :language: python
