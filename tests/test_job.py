# Contains tests specific to Jobs
import pytest
import requests
from utils import function_called_raiser

from astrometry_net_client import Job
from astrometry_net_client.exceptions import (
    StatusFailedException,
    StillProcessingException,
)


@pytest.mark.mocked
def test_mocked_job_status_success(mock_server, monkeypatch):
    job = Job(1)

    assert hash(job) == hash(1)
    # No status queried yet
    assert not job.done()
    assert not job.success()

    response = job.status()

    assert job.done()
    assert job.success()
    assert response == {"status": "success"}
    assert job.resp_status == "success"

    info = job.info()
    assert info is not None
    assert isinstance(info, dict)
    assert info["status"] == "success"

    for key in info.keys():
        print(f"{key=}")
        assert hasattr(job, key)
        if key != "status":
            assert getattr(job, key) == info[key]

    # Test caching of info(). If get is used, throw exception.
    monkeypatch.setattr(requests, "get", function_called_raiser)

    # No new request should be made!
    cached_info = job.info()
    assert cached_info is info


@pytest.mark.mocked
def test_mocked_job_status_failure(mock_server):
    job = Job(0)

    # No status queried yet
    assert not job.done()
    assert not job.success()

    response = job.status()

    assert response == {"status": "failure"}
    assert job.resp_status == "failure"
    assert job.done()
    assert not job.success()

    # Should have this exception
    with pytest.raises(StatusFailedException):
        job.info()


def test_job_still_solving(mock_server):
    job = Job(2)

    with pytest.raises(StillProcessingException):
        job.info()

    job_2 = Job(3)
    with pytest.raises(StillProcessingException):
        job_2.wcs_file()


def test_job_timeout(mock_server):
    job = Job(2)
    with pytest.raises(TimeoutError):
        job.until_done(timeout=0)  # immediate timeout

    job_2 = Job(3)
    with pytest.raises(TimeoutError):
        # timeout after two queries
        job_2.until_done(start=1, end=1, timeout=2)
