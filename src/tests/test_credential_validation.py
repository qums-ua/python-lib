"""Tests for Client input validation (no network required)."""

import pytest

from qums_fetch import Client


def test_empty_username_raises_valueerror():
    with pytest.raises(ValueError, match="Username and password are required"):
        Client("", "somepassword", auto_login=False)


def test_empty_password_raises_valueerror():
    with pytest.raises(ValueError, match="Username and password are required"):
        Client("someuser", "", auto_login=False)


def test_both_empty_raises_valueerror():
    with pytest.raises(ValueError, match="Username and password are required"):
        Client("", "", auto_login=False)


def test_valid_credentials_no_login():
    client = Client("testuser", "testpass", auto_login=False)
    assert not client.is_logged_in


def test_zero_retries_raises_valueerror():
    with pytest.raises(ValueError, match="login_retries must be greater than 0"):
        Client("testuser", "testpass", login_retries=0, auto_login=False)


def test_negative_retries_raises_valueerror():
    with pytest.raises(ValueError, match="login_retries must be greater than 0"):
        Client("testuser", "testpass", login_retries=-1, auto_login=False)
