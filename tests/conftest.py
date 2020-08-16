import pytest
import requests

from astrometry_net_client import Job


class MockJobStatusResponseSuccess:

    _response = {"status": "success"}
    headers = {"Content-Type": "text/plain"}
    status_code = 200

    @staticmethod
    def text():
        return str(MockJobStatusResponseSuccess._response)

    @staticmethod
    def json():
        return MockJobStatusResponseSuccess._response


@pytest.fixture
def mock_job_status(monkeypatch):
    def mock_get(*args, **kwargs):
        return MockJobStatusResponseSuccess()

    monkeypatch.setattr(requests, "get", mock_get)


@pytest.fixture
def success_job():
    job = Job(4446851)
    return job


@pytest.fixture
def failed_job():
    job = Job(4450465)
    return job
