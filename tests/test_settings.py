import pytest

from astrometry_net_client import Settings


def test_dict():
    """
    Test normal behaviour of the settings object, using multiple access
    mechanisms.
    """
    # Creating 'new' settings
    settings = Settings(parity=2)
    settings.image_width = 1000
    settings["image_height"] = 2000
    settings.update({"publicly_visible": "y", "use_sextractor": True})

    assert settings == {
        "publicly_visible": "y",
        "use_sextractor": True,
        "parity": 2,
        "image_width": 1000,
        "image_height": 2000,
    }, "Initialization incorrect"

    # Modification of the settings object
    del settings["parity"]
    settings.use_sextractor = False
    settings["publicly_visible"] = "n"
    settings.update({"image_height": 500, "image_width": 1000})

    assert settings == {
        "publicly_visible": "n",
        "use_sextractor": False,
        "image_width": 1000,
        "image_height": 500,
    }, "Modifications or deletions not applied properly"


def test_range():
    """
    Test the range convenience functions
    """
    settings = Settings()
    settings.set_scale_range(10, 20)
    assert settings == {
        "scale_lower": 10,
        "scale_upper": 20,
        "scale_units": "arcminwidth",
        "scale_type": "ul",
    }

    settings2 = Settings()
    settings2.set_scale_estimate(15, 5)
    assert settings2 == {
        "scale_est": 15,
        "scale_err": 5,
        "scale_units": "arcminwidth",
        "scale_type": "ev",
    }

    settings2 = Settings()
    settings2.set_scale_estimate(150, 5, unit="degwidth")
    assert settings2 == {
        "scale_est": 150,
        "scale_err": 5,
        "scale_units": "degwidth",
        "scale_type": "ev",
    }


def test_validation():
    """
    Tests all the validation mechanisms, where there should be an error msg
    """
    settings = Settings()

    # not a valid name for a setting
    with pytest.raises(KeyError) as e:
        settings.invalid_name = 10
    assert "invalid_name is not an allowed setting." in str(e.value)

    # valid name, but invalid type
    with pytest.raises(TypeError) as e:
        settings.scale_lower = "a string"  # expects float
    assert "Value does not have the correct type" in str(e.value)

    # valid name, but invalid type
    with pytest.raises(TypeError) as e:
        settings.image_height = 10.5  # float, expects int
    assert "Value does not have the correct type" in str(e.value)

    with pytest.raises(TypeError) as e:
        settings.allow_modifications = 0  # expects str
    assert "Value does not have the correct type" in str(e.value)

    # valid name, valid type, invalid value
    with pytest.raises(ValueError) as e:
        settings.allow_commercial_use = "invalid"
    assert "Value invalid is not allowed for the setting" in str(e.value)

    # valid name, valid type, invalid value
    with pytest.raises(ValueError) as e:
        settings.set_scale_range(0, 20, unit="invalid")
    assert "Value invalid is not allowed for the setting" in str(e.value)

    with pytest.raises(TypeError) as e:
        settings.set_scale_range(0, "invalid")
    assert "Value does not have the correct type" in str(e.value)

    with pytest.raises(TypeError) as e:
        settings.set_scale_range("invalid", 20)
    assert "Value does not have the correct type" in str(e.value)

    # make sure nothing is actually set!
    assert settings == {}, "Settings dict is not empty, but should be."


def test_data_override():
    """
    Make sure the data attribute is still accessible and does not give an error
    """
    settings = Settings()
    assert isinstance(settings.data, dict)
