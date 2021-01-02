from constants import FILE, VALID_KEY

from astrometry_net_client import FileUpload, Session


def test_upload(mock_server):
    session = Session(VALID_KEY)

    upl = FileUpload(FILE, session)
    assert upl.filename == FILE

    submission = upl.submit()

    assert submission.id == 2
    assert not submission.done()
    assert not submission.success()

    submission.status()

    assert not submission.done()
    assert not submission.success()

    submission.until_done()

    assert submission.done()
    job = submission.jobs[0]

    assert job.id == 2
    assert not job.done()

    job.until_done()

    assert job.done()
    assert job.success()
    assert submission.success()


def test_upload_until_done(mock_server):
    session = Session(VALID_KEY)
    upl = FileUpload(FILE, session)
    submission = upl.submit()
    submission.until_done()
    assert submission.done()

