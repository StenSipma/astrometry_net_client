import pytest

from astropy.io.fits import Header
from astrometry_net_client.exceptions import StatusFailedException
from astrometry_net_client import Session, FileUpload, Submission


@pytest.mark.online
def test_job_status_success(success_job):
    response = success_job.status()
    assert success_job.done()
    assert success_job.success()
    assert response == {"status": "success"}
    assert success_job.resp_status == "success"

    wcs = success_job.wcs_file()
    assert isinstance(wcs, Header)


@pytest.mark.online
def test_job_status_failed(failed_job):
    response = failed_job.status()

    assert failed_job.done()
    assert not failed_job.success()
    assert response == {"status": "failure"}
    assert failed_job.resp_status == "failure"

    with pytest.raises(StatusFailedException):
        failed_job.wcs_file()


@pytest.mark.online
@pytest.mark.long
def test_old():
    # TODO: verify if this function is still correct & all tests pass

    # WARNING: makes an upload and then waits for the upload to be done.
    #          do not spam this test!

    # key in project root
    session = Session(None, key_location="./key")
    assert not session.logged_in

    session.login()
    assert session.logged_in

    # TODO include some test data in the repository
    upl = FileUpload(
        "../test-data/target.200417.00000088.3x3.FR.fits", session=session
    )

    submission = upl.submit()
    assert isinstance(submission, Submission)

    assert not submission.done()
    assert len(submission.jobs) == 0
    resp = submission.status()
    assert not submission.done()
    assert submission.jobs[0] is None

    resp = submission.until_done()
    assert submission.done()

    status_attrs = [
        "start",
        "user_images",
        "processing_started",
        "processing_finished",
        "job_calibrations",
    ]
    for attr in status_attrs:
        assert hasattr(submission, attr), f"Submission does not have {attr}"

    for job in submission:
        assert not job.done()
        assert not job.success()

        resp = job.status()
        assert not job.done()
        assert not job.success()

        resp = job.until_done()
        assert job.done()
        assert job.success()

        resp = job.info()
        assert resp["status"] == "success"
        assert resp.resp_status == "success"
        assert resp.calibration is not None

        wcs = job.wcs_file()
        assert isinstance(wcs, Header)
