import os
from unittest import mock

import pytest
import requests
from constants import VALID_KEY
from utils import FunctionCalledException, function_called_raiser

from astrometry_net_client import Session
from astrometry_net_client.exceptions import APIKeyError, LoginFailedException

some_key = "somekey"


# Start of tests
def test_session_key_input_invalid():
    with pytest.raises(APIKeyError):
        Session()


def test_session_key_input_string():
    s = Session(some_key)
    assert not s.logged_in
    assert s.api_key == some_key


def test_session_key_input_file():
    s = Session(key_location="./tests/data/testkey")
    assert not s.logged_in
    assert s.api_key == some_key


@mock.patch.dict(os.environ, {"ASTROMETRY_API_KEY": some_key})
def test_session_key_input_environment():
    s = Session()
    assert not s.logged_in
    assert s.api_key == some_key


def test_valid_session_login(mock_server, monkeypatch):
    session = Session(api_key=VALID_KEY)
    session.login()  # login for the first time
    assert session.logged_in
    assert getattr(session, "key", None)  # token exists
    original_key = session.key

    # We patch the post call to send an error if it is called.
    monkeypatch.setattr(requests, "post", function_called_raiser)

    session.login()  # login should not be done now, as it is already done
    assert session.logged_in
    assert session.key == original_key

    # Here we force the login which should raise the patched exception
    with pytest.raises(FunctionCalledException):
        session.login(force=True)


def test_invalid_session_login(mock_server):
    session = Session(api_key="invalid_key")
    with pytest.raises(LoginFailedException):
        session.login()
