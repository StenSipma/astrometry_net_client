import pytest

from astrometry_net_client import Job


@pytest.mark.mocked
def test_mocked_job_status_success(mock_status):
    job = Job(1)

    # No status queried yet
    assert not job.done()
    assert not job.success()

    response = job.status()

    assert job.done()
    assert job.success()
    assert response == {"status": "success"}
    assert job.resp_status == "success"


@pytest.mark.mocked
def test_mocked_job_status_failure(mock_status):
    job = Job(0)

    # No status queried yet
    assert not job.done()
    assert not job.success()

    response = job.status()

    assert response == {"status": "failure"}
    assert job.resp_status == "failure"
    assert job.done()
    assert not job.success()
