import pytest
from unittest import mock
import os
from itertools import repeat

from constants import VALID_KEY, FILE
from astrometry_net_client import Client, Session, Settings
from astrometry_net_client.exceptions import LoginFailedException

some_key = "somekey"


@mock.patch.dict(os.environ, {"ASTROMETRY_API_KEY": VALID_KEY})
def test_client_login_env(mock_server):
    c = Client()
    assert c.session.logged_in


def test_client_login(mock_server):
    c = Client(api_key=VALID_KEY)
    assert c.session.logged_in

    with pytest.raises(LoginFailedException):
        c = Client(key_location="./tests/data/testkey")

    c = Client(session=Session(VALID_KEY))
    assert c.session.logged_in


def test_client_settings(mock_server):
    settings = Settings(
        use_sextractor=True, image_height=1000, image_width=2000
    )
    client = Client(settings=settings, api_key=VALID_KEY)
    client2 = Client(
        use_sextractor=True,
        image_height=1000,
        image_width=2000,
        api_key=VALID_KEY,
    )
    assert client.settings == {
        "use_sextractor": True,
        "image_height": 1000,
        "image_width": 2000,
    }
    assert client.settings == client2.settings


def test_client_upload_filter(mock_server):
    client = Client(api_key=VALID_KEY)

    job = client.filtered_upload_wrapper(FILE, filter_func=lambda x: False)
    assert job is None


@pytest.mark.long
def test_client_upload(mock_server):
    client = Client(api_key=VALID_KEY)

    job = client.upload_file(FILE)
    assert job.success()
    assert job.done()

    # should be normal
    job = client.filtered_upload_wrapper(FILE)
    assert job is not None
    assert job.success()
    assert job.done()


@pytest.mark.long
def test_client_upload_multiple(mock_server):
    client = Client(api_key=VALID_KEY)
    jobs = client.upload_files_gen([FILE] * 5, workers=3)

    assert jobs is not None

    for job, filename in jobs:
        assert filename == FILE
        assert job.done()
        assert job.success()

