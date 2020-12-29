import json

import pytest
import requests
from constants import (
    FAILED_SUBMISSION_RESULT,
    SUCCESS_SUBMISSION_RESULT,
    VALID_KEY,
)

from astrometry_net_client import Job, Submission


class ResponseObj:
    def __init__(self, response, headers, status_code=200):
        self._response = response
        self.headers = headers
        self.status_code = status_code

    def text(self):
        return str(self._response)

    def json(self):
        return self._response


class MockGetRequest:
    _response = {}
    headers = {"Content-Type": "text/plain"}
    status_code = 200

    def __call__(self, *args, **kwargs):
        return ResponseObj(self._response, self.headers, self.status_code)


class MockSessionChecker:
    headers = {"Content-Type": "text/plain"}

    def __call__(self, url, data, **kwargs):
        payload = json.loads(data["request-json"])
        if payload.get("apikey", "") == VALID_KEY:
            response = {
                "status": "success",
                "session": "the session token/key",
            }
        else:
            response = {"status": "error", "errormessage": "bad apikey"}
        return ResponseObj(response, self.headers)


@pytest.fixture
def mock_session(monkeypatch):
    monkeypatch.setattr(requests, "post", MockSessionChecker())


# Jobs
class MockJobStatusResponseSuccess(MockGetRequest):
    _response = {"status": "success"}


class MockJobStatusResponseFailed(MockGetRequest):
    _response = {"status": "faillure"}


@pytest.fixture
def mock_job_status(monkeypatch):
    monkeypatch.setattr(requests, "get", MockJobStatusResponseSuccess())


# Submissions
class MockSubmissionResponseFailed(MockGetRequest):
    _response = FAILED_SUBMISSION_RESULT

    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        if self.calls > 1:
            return MockJobStatusResponseFailed()(*args, **kwargs)
        return super().__call__(*args, **kwargs)


class MockSubmissionResponseSuccess(MockGetRequest):
    _response = SUCCESS_SUBMISSION_RESULT

    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        if self.calls > 1:
            return MockJobStatusResponseSuccess()(*args, **kwargs)
        return super().__call__(*args, **kwargs)


@pytest.fixture
def mock_submission_status_success(monkeypatch):
    monkeypatch.setattr(requests, "get", MockSubmissionResponseSuccess())


@pytest.fixture
def mock_submission_status_failed(monkeypatch):
    monkeypatch.setattr(requests, "get", MockSubmissionResponseFailed())


## Online fixtures
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
