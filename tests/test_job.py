import pytest
from astropy.io.fits import Header

from astrometry_net_client.exceptions import StatusFailedException
from astrometry_net_client.statusables import Job


@pytest.mark.mocked
def test_mocked_job_status_success(mock_job_status):
    success_job = Job(0)
    response = success_job.status()
    assert success_job.done()
    assert success_job.success()
    assert response == {"status": "success"}
    assert success_job.resp_status == "success"


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
