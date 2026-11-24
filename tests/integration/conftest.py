import os

import pytest
from dotenv import load_dotenv

from qums_fetch import Client


@pytest.fixture(scope="session")
def client() -> Client:
    load_dotenv()
    username = os.getenv("QUMS_USERNAME")
    password = os.getenv("QUMS_PASSWORD")
    if not username or not password:
        pytest.skip("QUMS credentials are not set.")

    return Client(username, password)
