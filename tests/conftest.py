import json

import pytest
import requests
from constants import VALID_KEY

from astrometry_net_client import Job


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
    headers = {}
    status_code = 500

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


class MockStatusResponseSuccess(MockGetRequest):
    _response = {"status": "success"}
    headers = {"Content-Type": "text/plain"}
    status_code = 200


@pytest.fixture
def mock_session(monkeypatch):
    monkeypatch.setattr(requests, "post", MockSessionChecker())


@pytest.fixture
def mock_job_status(monkeypatch):
    monkeypatch.setattr(requests, "get", MockStatusResponseSuccess())


# Online fixtures
@pytest.fixture
def success_job():
    job = Job(4446851)
    return job


@pytest.fixture
def failed_job():
    job = Job(4450465)
    return job
