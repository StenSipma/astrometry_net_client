import json

import pytest
import requests
from astropy.io import fits
from constants import (
    FAILED_SUBMISSION_RESULT,
    FILE,
    JOB_INFO,
    STATUS_FAILURE,
    STATUS_SUCCESS,
    SUCCESS_SUBMISSION_RESULT,
    SUCCESS_SUBMISSION_RESULT_2,
    VALID_KEY,
    VALID_TOKEN,
    WAITING_SUBMISSION_RESULT,
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
                "session": VALID_TOKEN,
            }
        else:
            response = {"status": "error", "errormessage": "bad apikey"}
        return ResponseObj(response)


class MockDelayedRequest(MockGetRequest):
    _wait = {"status": "solving"}

    def __init__(self, *args, wait_content=None, delays=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.delays = delays
        self.wait_content = wait_content if wait_content else self._wait
        self.done_content = self._response
        self._response = self.wait_content

    def __call__(self, *args, **kwargs):
        if self.delays > 0:
            self.delays -= 1
        else:
            self._response = self.done_content
        return super().__call__(*args, **kwargs)


class MockUpload:
    def __call__(self, url, data, **kwargs):
        payload = json.loads(data["request-json"])
        if payload["session"] != VALID_TOKEN:
            # TODO: use correct error message
            return ResponseObj(
                {"status": "error", "errormessage": "no session with key"}
            )

        upload_file = kwargs["files"]["file"]
        print(upload_file)

        request_hdul = fits.HDUList(file=upload_file)
        with open(FILE, "rb") as reffile:
            reference_hdul = fits.HDUList(file=reffile)

        assert request_hdul == reference_hdul

        return ResponseObj(
            {
                "status": "success",
                "subid": 2,
                # "hash": "6024b45a16bfb5af7a73735cbabdf2b462c11214",
            }
        )


# Submissions
@pytest.fixture
def mock_server(monkeypatch):
    get_mapper = {
        "/api/submissions/0": MockGetRequest(FAILED_SUBMISSION_RESULT),
        "/api/submissions/1": MockGetRequest(SUCCESS_SUBMISSION_RESULT),
        "/api/submissions/2": MockDelayedRequest(
            content=SUCCESS_SUBMISSION_RESULT_2,
            wait_content=WAITING_SUBMISSION_RESULT,
        ),
        "/api/jobs/0": MockGetRequest(STATUS_FAILURE),
        "/api/jobs/1": MockGetRequest(STATUS_SUCCESS),
        "/api/jobs/2": MockDelayedRequest(STATUS_SUCCESS),
        "/api/jobs/3": MockDelayedRequest(STATUS_SUCCESS, delays=10),
        "/api/jobs/4819815": MockGetRequest(STATUS_FAILURE),
        "/api/jobs/4489363": MockGetRequest(STATUS_SUCCESS),
        "/api/jobs/1/info": MockGetRequest(JOB_INFO),
        "/api/jobs/4489363/info": MockGetRequest(JOB_INFO),
    }

    post_mapper = {
        "/api/login": MockSessionChecker(),
        "/api/upload": MockUpload(),
    }

    svr = MockServer(get=get_mapper, post=post_mapper)

    monkeypatch.setattr(requests, "get", svr.get)
    monkeypatch.setattr(requests, "post", svr.post)


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
