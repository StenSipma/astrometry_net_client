from collections import UserDict, namedtuple

# TODO idea, replace the settings with descriptors ?
#      e.g. an angle descriptor, which can handle astropy units
#      and convert to the appropriate units (e.g. if radians are given)

# TODO idea, read settings from some file for persistent use.

Setting = namedtuple("Setting", "name type verify_func", defaults=(None,))

_allowed_settings = {
    Setting("allow_commercial_use", str, lambda x: x in {"d", "y", "n"}),
    Setting("allow_modifications", str, lambda x: x in {"d", "y", "n", "sa"}),
    Setting("publicly_visible", str, lambda x: x in {"y", "n"}),
    Setting(
        "scale_units",
        str,
        lambda x: x in {"degwidth", "arcminwidth", "arcsecperpix"},
    ),
    Setting("scale_type", str, lambda x: x in {"ul", "ev"}),
    Setting("scale_lower", float),
    Setting("scale_upper", float),
    Setting("scale_est", float),
    Setting("scale_err", float, lambda x: x >= 0.0 and x <= 100.0),
    Setting("center_ra", float, lambda x: x >= 0.0 and x <= 360.0),
    Setting("center_dec", float, lambda x: x >= -90.0 and x <= 90.0),
    Setting("radius", float),
    Setting("downsample_factor", float, lambda x: x > 1),
    Setting("tweak_order", int),
    Setting("use_sextractor", bool),
    Setting("crpix_center", bool),
    Setting("parity", int, lambda x: x in {0, 1, 2}),
    Setting("image_width", int),
    Setting("image_height", int),
    Setting("positional_error", float),
}


class Settings(UserDict):
    """
    Enhanced dictionary which stores the parameters which can be given
    alongside a request (mainly upload requests like
    :py:class:astrometry_net_client.upload.UploadFile)

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
    >>> settings['image_height'] = 2000
    >>> settings
    {'parity': 2, 'image_width': 1000, 'image_height': 2000}
    >>> settings.set_scale_range(10, 20)
    >>> settings
    {'parity': 2, 'image_width': 1000, 'image_height': 2000,
            'scale_lower': 10, 'scale_upper': 20, 'scale_units': 'arcminwidth',
            'scale_type': 'ul'}
    """

    _settings = {s.name: s for s in _allowed_settings}

    def __setitem__(self, key, value):
        error_msg = ""
        if key not in Settings._settings:
            msg = "{} is not an allowed setting. Must be one of: {}"
            error_msg = msg.format(key, Settings._settings)
        elif not isinstance(value, Settings._settings[key].type):
            msg = "Value does not have the correct type. Excpected {} was {}"
            error_msg.format(Settings._settings[key].type, type(value))

        elif Settings._settings[key].verify_func and not Settings._settings[
            key
        ].verify_func(value):
            error_msg = f"Value {value} is not allowed for the setting {key}."

        if error_msg:
            raise KeyError(error_msg)

        self.data[key] = value

    def __setattr__(self, name, value):
        if name == "data":
            return super().__setattr__(name, value)
        return self.__setitem__(name, value)

    def set_scale_range(self, lower, upper, unit="arcminwidth"):
        """
        Specify the size of your field using a range.

        Set the upper and lower limits for the field size of your upload. The
        unit is defined by the ``unit`` parameter, which defaults to
        ``'arcminwidth'``.

        Incompatible with :py:func:`set_scale_estimate`

        Example
        -------
        >>> settings = Settings()
        >>> settings.set_scale_range(5, 25)
        >>> settings
        {'scale_lower': 5, 'scale_upper': 25, 'scale_units': 'arcminwidth',
                'scale_type': 'ul'}

        Parameters
        ----------
        lower: float
            Number which defines the lowest value for your field size.
        upper: float
            Number which defines the highest value for your field size.
        unit: str
            Optional argument which determines the unit of the ``upper`` /
            ``lower`` values. Defaults to ``'arcminwidth'``. Can be one of:
            ``'arcminwidth'``,``arcsecperpix`` or ``'degwidth'``.
        """
        self.scale_lower = lower
        self.scale_upper = upper
        self.scale_units = unit
        self.scale_type = "ul"

    def set_scale_estimate(self, estimate, error, unit="arcminwidth"):
        """
        Specify the size of your field using an estimate + a deviation (error)

        Sets the size of your field by an estimate + error pair. Will result in
        a range of (estimate - error, estimate + error).

        Incompatible with :py:func:`set_scale_range`

        Example
        -------
        >>> settings = Settings()
        >>> settings.set_scale_estimate(15, 5)
        >>> settings
        {'scale_est': 15, 'scale_err': 5, 'scale_units': 'arcminwidth',
                'scale_type': 'ev'}

        Parameters
        ----------
        estimate: float
            The estimate center value for your field size.
        error: float
            The range around your estimate value.
        unit: str
            Optional argument which determines the unit of the ``upper`` /
            ``lower`` values. Defaults to ``'arcminwidth'``. Can be one of:
            ``'arcminwidth'``,``arcsecperpix`` or ``'degwidth'``.
        """
        self.scale_est = estimate
        self.scale_err = error
        self.scale_units = unit
        self.scale_type = "ev"
