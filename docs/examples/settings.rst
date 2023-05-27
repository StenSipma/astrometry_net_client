Settings
========

There are multiple settings available to edit properties of the upload (see
table below). They can be given to any
:py:class:`astrometry_net_client.settings.Settings` using the following code:

.. code-block:: python

   from astrometry_net_client import Settings

   s = Settings()
   # Replace 'option_keyword' with the option and 'value' with the value you want
   s.option_keyword = value 

The most useful options are related to the scale of the image (``scale_*``) and
the coordinates associated with the center of the image (``center_ra``,
``center_dec`` and ``radius``). The scale options are not straightforward, so
there are some helper functions to make setting these options easier:

 - :py:func:`astrometry_net_client.settings.Settings.set_scale_estimate`
 - :py:func:`astrometry_net_client.settings.Settings.set_scale_range`

Examples
********

For all the below examples, we assume the variable ``settings`` is the
``Settings`` object.

1. We know the plate scale of our CCD (it is 0.566 arcseconds per pixel). We can
   set this information like this:

        .. code-block:: python

           settings.set_scale_estimate(0.566, 10, unit="arcsecperpix")

  Setting this, constraints the search space of Astrometry to only 0.566 +-
  10%. Instead of setting a percentage around the value, we can also give it a
  manual range of +- 0.005 around the central value:

        .. code-block:: python

           settings.set_scale_range(0.561, 0.571, unit="arcsecperpix")

2. We took images of M51, so we approximately know the coordinates of the
   central pixels are around (ra, dec) 13h 29m 52.7s, +47° 11′ 43″. We first
   need to convert this to degrees: (202.47, 47.20). We also need to specify a
   radius of uncertainy in which to search, and to be safe we set it to 1
   degree (this depends on the FoV of your telescope). Note, that we always need
   to specify all three options for the settings to apply!

        .. code-block:: python

           settings.center_ra = 202.47 # degrees
           settings.center_dec = 47.20 # degrees
           settings.radius = 1 # degree






Table of Settings
*****************

These are the direct arguments which can be passed to the API, for a complete
description of them see http://astrometry.net/doc/net/api.html#submitting-a-url.

.. list-table:: Settings
   :header-rows: 1

   * - Option Keyword
     - Type
     - Constraint

   * - ``scale_units``
     - str
     - Must be one of: 'degwidth', 'arcminwidth', 'arcsecperpix'

   * - ``scale_type``
     - str
     - Must be one of: 'ul', 'ev'

   * - ``scale_lower``
     - float
     - 

   * - ``scale_upper``
     - float
     - 

   * - ``scale_est``
     - float
     - 

   * - ``scale_err``
     - float
     - Must be in range [0.0, 100.0]

   * - ``center_ra``
     - float
     - Degrees: Must be in range [0.0, 360.0]

   * - ``center_dec``
     - float
     - Degrees: Must be in range [-90.0, 90.0]

   * - ``radius``
     - float
     - Degrees

   * - ``downsample_factor``
     - float
     - Must be greater or equal to 1

   * - ``tweak_order``
     - int
     - 

   * - ``use_sextractor``
     - bool
     - 

   * - ``crpix_center``
     - bool
     - 

   * - ``parity``
     - int
     - Must be one of 0, 1, 2

   * - ``image_width``
     - int
     - 

   * - ``image_height``
     - int
     - 

   * - ``positional_error``
     - float
     - 

   * - ``allow_commercial_use``
     - str
     - Must be one of: 'd', 'y', 'n'

   * - ``allow_modifications``
     - str
     - Must be one of: 'd', 'y', 'n', 'sa'

   * - ``publicly_visible``
     - str
     - Must be: 'y' or 'n'
