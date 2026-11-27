import json
from collections.abc import Callable
from unittest.mock import Mock

import pytest
import requests


@pytest.fixture
def response() -> Callable[..., requests.Response]:
    def make_response(body: str, status: int = 200) -> requests.Response:
        result = requests.Response()
        result.status_code = status
        result._content = body.encode()
        return result

    return make_response


@pytest.fixture
def records(
    response: Callable[..., requests.Response],
) -> Callable[..., requests.Response]:
    def make_records(**fields: object) -> requests.Response:
        return response(
            json.dumps({key: json.dumps(value) for key, value in fields.items()})
        )

    return make_records


@pytest.fixture
def post(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock()
    monkeypatch.setattr(requests.Session, "post", mock)
    return mock
