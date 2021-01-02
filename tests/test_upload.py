import pytest

from astrometry_net_client import FileUpload, Session
from constants import VALID_KEY, FILE


def test_upload(mock_server):
    session = Session(VALID_KEY)

    upl = FileUpload(FILE, session)
    assert upl.filename == FILE

    submission = upl.submit()

    assert submission.id == 2
    assert not submission.done()
    assert not submission.success()

    submission.until_done()

    assert submission.done()
    assert submission.success()
