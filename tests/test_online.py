import pytest
from astropy.io.fits import Header

from astrometry_net_client import FileUpload, Job, Session, Submission
from astrometry_net_client.exceptions import StatusFailedException


@pytest.mark.online
def test_job_status_success(success_job: Job):
    response = success_job.status()
    assert success_job.done()
    assert success_job.success()
    assert response == {"status": "success"}
    assert success_job.resp_status == "success"

    wcs = success_job.wcs_file()
    assert isinstance(wcs, Header)


@pytest.mark.online
def test_job_status_failed(failed_job: Job):
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
    # TODO: does pass, but no checks done for consistency

    # WARNING: makes an upload and then waits for the upload to be done.
    #          do not spam this test!

    # key in project root
    session = Session(None, key_location="./key")
    assert not session.logged_in

    session.login()
    assert session.logged_in

    # TODO include some test data in the repository
    upl = FileUpload("../test/data/target.200417.00000088.3x3.FR.fits", session=session)

    submission = upl.submit()
    assert isinstance(submission, Submission)

    assert not submission.done()
    resp = submission.status()
    assert not submission.done()

    resp = submission.until_done()
    assert submission.done()

    status_attrs = [
        "processing_started",
        "processing_finished",
        "user_images",
        "user",
        "images",
        "job_calibrations",
    ]
    for attr in status_attrs:
        assert hasattr(submission, attr), f"Submission does not have {attr}"

    assert len(submission.jobs) > 0
    for job in submission:
        resp = job.until_done()
        assert job.done()
        assert job.success()

        resp = job.info()
        assert resp["status"] == "success"
        assert job.resp_status == "success"
        assert job.calibration is not None

        wcs = job.wcs_file()
        assert isinstance(wcs, Header)
