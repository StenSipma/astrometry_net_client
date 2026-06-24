import os
from unittest import mock
from unittest.mock import MagicMock

import pytest
from constants import FILE, VALID_KEY

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
    settings = Settings(use_sextractor=True, image_height=1000, image_width=2000)
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


@pytest.mark.long
def test_client_upload(mock_server):
    client = Client(api_key=VALID_KEY)

    job = client.upload_file(FILE)
    assert job.success()
    assert job.done()


@pytest.mark.long
def test_client_upload_multiple(mock_server):
    client = Client(api_key=VALID_KEY)
    jobs = client.upload_files_gen([FILE] * 5, queue_size=3)

    assert jobs is not None

    for job, filename in jobs:
        assert filename == FILE
        assert job.done()
        assert job.success()


@pytest.mark.mocked
def test_upload_files_gen_correct_filenames(mock_server, monkeypatch):
    """Each yielded filename must match the file whose job finished, not the next queued file."""
    client = Client(api_key=VALID_KEY)

    def fake_insert(filename, queue):
        job = MagicMock()
        job.done.return_value = True
        submission = MagicMock()
        submission.done.return_value = True
        submission.jobs = [job]
        queue.put((filename, submission, job))

    monkeypatch.setattr(client, "_insert_submission", fake_insert)

    files = ["file_a.fits", "file_b.fits"]
    results = list(client.upload_files_gen(files, queue_size=1))

    yielded_filenames = {filename for _, filename in results}
    assert yielded_filenames == set(files)


@pytest.mark.mocked
def test_upload_file_doesnt_mutate_client_settings(mock_server, monkeypatch):
    """Per-upload settings must not leak into the client's default settings."""
    client = Client(api_key=VALID_KEY)
    assert "parity" not in client.settings

    fake_submission = MagicMock()
    fake_submission.jobs = [MagicMock()]
    monkeypatch.setattr(
        "astrometry_net_client.client.FileUpload.submit", lambda self: fake_submission
    )

    client.upload_file(FILE, settings=Settings(parity=2))

    assert "parity" not in client.settings
