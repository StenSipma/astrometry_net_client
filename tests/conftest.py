import json

import pytest
import requests
from constants import (
    FAILED_SUBMISSION_RESULT,
    STATUS_FAILURE,
    STATUS_SUCCESS,
    SUCCESS_SUBMISSION_RESULT,
    VALID_KEY,
    JOB_INFO,
)
from mocked_server import MockServer, ResponseObj

from astrometry_net_client import Job, Submission


class MockGetRequest:
    _response = {}
    headers = {"Content-Type": "text/plain"}

    def __init__(self, content=None, headers=None, status_code=200):
        self._response = content if content else self._response
        self.headers = headers if headers else self.headers
        self.status_code = status_code

    def __call__(self, *args, **kwargs):
        return ResponseObj(self._response, self.headers, self.status_code)


class MockSessionChecker:
    def __call__(self, url, data, **kwargs):
        payload = json.loads(data["request-json"])
        if payload.get("apikey", "") == VALID_KEY:
            response = {
                "status": "success",
                "session": "the session token/key",
            }
        else:
            response = {"status": "error", "errormessage": "bad apikey"}
        return ResponseObj(response)


@pytest.fixture
def mock_session(monkeypatch):
    monkeypatch.setattr(requests, "post", MockSessionChecker())


@pytest.fixture
def mock_job_status(monkeypatch):
    monkeypatch.setattr(requests, "get", ())


# Submissions
@pytest.fixture
def mock_status_success(monkeypatch):
    mapper = {
        "/api/submissions": MockGetRequest(SUCCESS_SUBMISSION_RESULT),
        "/api/jobs": MockGetRequest(STATUS_SUCCESS),
    }
    svr = MockServer(mapper)
    monkeypatch.setattr(requests, "get", svr.get)


@pytest.fixture
def mock_status_failure(monkeypatch):
    mapper = {
        "/api/submissions": MockGetRequest(FAILED_SUBMISSION_RESULT),
        "/api/jobs": MockGetRequest(STATUS_FAILURE),
    }
    svr = MockServer(mapper)
    monkeypatch.setattr(requests, "get", svr.get)


@pytest.fixture
def mock_status(monkeypatch):
    mapper = {
        "/api/submissions/0": MockGetRequest(FAILED_SUBMISSION_RESULT),
        "/api/submissions/1": MockGetRequest(SUCCESS_SUBMISSION_RESULT),
        "/api/jobs/0": MockGetRequest(STATUS_FAILURE),
        "/api/jobs/1": MockGetRequest(STATUS_SUCCESS),
        "/api/jobs/4819815": MockGetRequest(STATUS_FAILURE),
        "/api/jobs/4489363": MockGetRequest(STATUS_SUCCESS),
        "/api/jobs/1/info": MockGetRequest(JOB_INFO),
        "/api/jobs/4489363/info": MockGetRequest(JOB_INFO),
    }
    svr = MockServer(mapper)
    monkeypatch.setattr(requests, "get", svr.get)


# Online fixtures
@pytest.fixture
def success_job():
    job = Job(4446851)
    return job


@pytest.fixture
def failed_job():
    job = Job(4450465)
    return job


@pytest.fixture
def success_submission():
    subm = Submission(3781056)
    return subm


@pytest.fixture
def failed_submission():
    subm = Submission(4113880)
    return subm
