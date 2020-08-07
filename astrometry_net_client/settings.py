from collections import namedtuple

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
    TODO Add documentation
    """

    _allowed_settings_names = {s.name for s in _allowed_settings}
    _settings = _allowed_settings

    def __setitem__(self, key, value):
        if key not in Setting._allowed_settings_names:
            msg = "{} is not an allowed setting. Must be one of: {}"
            error_msg = msg.format(key, Setting._allowed_settings_names)
        elif not isinstance(value, Setting._settings[key].type):
            msg = "Value does not have the correct type. Excpected {} was[M G7"
        elif Settings._settings[key].verify_func and Setting._settings[
            key
        ].verify_func(value):
            pass

        if error_msg:
            raise KeyError(error_msg)
        self.data[key] = value
