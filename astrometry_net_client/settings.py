import numbers
from collections import UserDict
from typing import Callable, NamedTuple, Optional

# TODO idea, replace the settings with descriptors ?
# TODO  e.g. an angle descriptor, which can handle astropy units
# TODO  and convert to the appropriate units (e.g. if radians are given)

# TODO idea, read settings from some file for persistent use.

# TODO use the same format as the astroquery constraints


class Setting(NamedTuple):
    name: str
    type: Callable
    verify_func: Optional[Callable] = None
    verify_mesg: Optional[str] = None


_allowed_settings = {
    Setting(
        "allow_commercial_use",
        str,
        lambda x: x in {"d", "y", "n"},
        "Must be one of: d, y, n",
    ),
    Setting(
        "allow_modifications",
        str,
        lambda x: x in {"d", "y", "n", "sa"},
        "Must be one of: d, y, n, sa",
    ),
    Setting("publicly_visible", str, lambda x: x in {"y", "n"}, "Must be: y or n"),
    Setting(
        "scale_units",
        str,
        lambda x: x in {"degwidth", "arcminwidth", "arcsecperpix"},
        "Must be one of: 'degwidth', 'arcminwidth', 'arcsecperpix'",
    ),
    Setting(
        "scale_type",
        str,
        lambda x: x in {"ul", "ev"},
        "Must be one of: ul, ev",
    ),
    Setting("scale_lower", numbers.Real),
    Setting("scale_upper", numbers.Real),
    Setting("scale_est", numbers.Real),
    Setting(
        "scale_err",
        numbers.Real,
        lambda x: x >= 0.0 and x <= 100.0,
        "Must be in range [0.0, 100.0]",
    ),
    Setting(
        "center_ra",
        numbers.Real,
        lambda x: x >= 0.0 and x <= 360.0,
        "Must be in range [0.0, 360.0]",
    ),
    Setting(
        "center_dec",
        numbers.Real,
        lambda x: x >= -90.0 and x <= 90.0,
        "Must be in range [-90.0, 90.0]",
    ),
    Setting("radius", numbers.Real),
    Setting(
        "downsample_factor",
        numbers.Real,
        lambda x: x >= 1,
        "Must be greater or equal to 1",
    ),
    Setting("tweak_order", numbers.Integral),
    Setting("use_sextractor", bool),
    Setting("crpix_center", bool),
    Setting(
        "parity",
        numbers.Integral,
        lambda x: x in {0, 1, 2},
        "Must be one of 0, 1, 2",
    ),
    Setting("image_width", numbers.Integral),
    Setting("image_height", numbers.Integral),
    Setting("positional_error", numbers.Real),
}


class Settings(UserDict):
    """
    Enhanced dictionary which stores the parameters which can be given
    alongside a request (mainly upload requests like
    :py:class:`astrometry_net_client.upload.UploadFile`)

    The settings can either be accessed (retrieved or set) using the normal
    dictionary notation, or the dot notation (see example). If an invalid
    setting is given (e.g. not a known setting, value of the setting has an
    incompatible type or the value does not satisfy the checking function)

    Some convenience functions are provided for easy setting of the plate
    scale.

    Example
    -------
    >>> from astrometry_net_client.settings import Settings
    >>> settings = Settings(parity=2)
    >>> settings.image_width = 1000
    >>> settings["image_height"] = 2000
    >>> settings.update({"publicly_visible": "y", "use_sextractor": True})
    >>> settings
    {
        "publicly_visible": "y",
        "use_sextractor": True,
        "parity": 2,
        "image_width": 1000,
        "image_height": 2000,
    }
    >>> # Modification of the settings object
    >>> del settings["parity"]
    >>> settings.use_sextractor = False
    >>> settings["publicly_visible"] = "n"
    >>> settings.update({"image_height": 500, "image_width": 1000})
    >>> settings
    {
        "publicly_visible": "n",
        "use_sextractor": False,
        "image_width": 1000,
        "image_height": 500,
    }
    """

    _settings = {s.name: s for s in _allowed_settings}

    def __setitem__(self, key, value):
        if key not in Settings._settings:
            msg = "{} is not an allowed setting. Must be one of: {}"
            error_msg = msg.format(key, list(Settings._settings.keys()))
            raise KeyError(error_msg)

        setting = Settings._settings[key]

        if not isinstance(value, setting.type):
            msg = "Value does not have the correct type."
            msg += " Excpected {} was {}"
            error_msg = msg.format(setting.type, type(value))
            raise TypeError(error_msg)

        if setting.verify_func and not setting.verify_func(value):
            error_msg = "Value {} is not allowed for the setting {}: {}"
            raise ValueError(error_msg.format(value, key, setting.verify_mesg))

        self.data[key] = value

    def __setattr__(self, name, value):
        if name == "data":
            return super().__setattr__(name, value)
        return self.__setitem__(name, value)

    def set_scale_range(self, lower, upper, unit="arcminwidth"):
        """
        Specify the size of your field (units 'arcminwidth' or 'degwitdth') or
        the plate scale (unit 'arcsecperpix') using a range.

        Set the upper and lower limits for the field size of your upload. The
        unit is defined by the ``unit`` parameter, which defaults to
        ``'arcminwidth'``.

        Do not set the range too small, otherwise Astrometry might not be able
        to solve your upload.

        Incompatible with :py:func:`set_scale_estimate`

        Parameters
        ----------
        lower: float
            Number which defines the lowest value for your field size.
        upper: float
            Number which defines the highest value for your field size.
        unit: str
            Optional argument which determines the unit of the ``upper`` /
            ``lower`` values. Defaults to ``'arcminwidth'``. Can be one of:
            ``'arcminwidth'``, ``'arcsecperpix'`` or ``'degwidth'``.

        Examples
        --------
        >>> settings = Settings()
        >>> settings.set_scale_range(5, 25)
        >>> settings
        {'scale_lower': 5, 'scale_upper': 25, 'scale_units': 'arcminwidth',
                'scale_type': 'ul'}
        """
        # Make a tmp Settings object to verify correctness of arguments
        tmp = Settings()
        tmp.scale_units = unit
        tmp.scale_lower = lower
        tmp.scale_upper = upper
        tmp.scale_type = "ul"

        # Commit changes, only if all are valid (e.g. no exception was raised)
        self.update(tmp)

    def set_scale_estimate(self, estimate, error, unit="arcminwidth"):
        """
        Specify the size of your field using an estimate + a deviation (error)

        Sets the size of your field by an estimate + error pair. The estimate
        is the central value, and the error (given in percent) specifies the
        deviation around this value.

        Do not set the error too low, otherwise Astrometry might not be able to
        solve your upload.

        Incompatible with :py:func:`set_scale_range`

        Parameters
        ----------
        estimate: float
            The estimate center value for your field size.
        error: float
            The range around your estimate value.
        unit: str
            Optional argument which determines the unit of the ``upper`` /
            ``lower`` values. Defaults to ``'arcminwidth'``. Can be one of:
            ``'arcminwidth'``, ``'arcsecperpix'`` or ``'degwidth'``.

        Examples
        --------
        >>> settings = Settings()
        >>> settings.set_scale_estimate(15, 5)
        >>> settings
        {'scale_est': 15, 'scale_err': 5, 'scale_units': 'arcminwidth',
                'scale_type': 'ev'}

        """
        # TODO refactor into a decorator, or make some verify function

        # Make a tmp Settings object to verify correctness of arguments
        tmp = Settings()
        tmp.scale_units = unit
        tmp.scale_est = estimate
        tmp.scale_err = error
        tmp.scale_type = "ev"

        # Commit changes, only if all are valid (e.g. no exception was raised)
        self.update(tmp)
