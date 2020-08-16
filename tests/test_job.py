import pytest

from astrometry_net_client import Job


@pytest.mark.mocked
def test_mocked_job_status_success(mock_job_status):
    success_job = Job(0)
    response = success_job.status()
    assert success_job.done()
    assert success_job.success()
    assert response == {"status": "success"}
    assert success_job.resp_status == "success"
