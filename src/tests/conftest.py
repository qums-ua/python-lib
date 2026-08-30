"""Shared fixtures for integration tests."""

import os

import pytest
from dotenv import load_dotenv

from qums_fetch import Client

load_dotenv()

QUMS_USERNAME = os.getenv("QUMS_USERNAME")
QUMS_PASSWORD = os.getenv("QUMS_PASSWORD")

pytestmark = pytest.mark.skipif(
    not (QUMS_USERNAME and QUMS_PASSWORD),
    reason="QUMS credentials not set in .env",
)


@pytest.fixture(scope="session")
def client():
    c = Client(QUMS_USERNAME, QUMS_PASSWORD)
    assert c.is_logged_in, "Client failed to log in"
    return c
