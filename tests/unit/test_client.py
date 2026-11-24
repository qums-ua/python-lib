import json
from unittest.mock import Mock

import pytest
import requests

from qums_fetch import CaptchaChallenge, Client, InvalidResponseError
from qums_fetch.client import BASE_URL


def response(body: str, status: int = 200) -> requests.Response:
    result = requests.Response()
    result.status_code = status
    result._content = body.encode()
    return result


def records(**fields: object) -> requests.Response:
    return response(
        json.dumps({key: json.dumps(value) for key, value in fields.items()})
    )


@pytest.fixture
def post(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock()
    monkeypatch.setattr(requests.Session, "post", mock)
    return mock


def test_direct_fetch_loads_student_details_after_login(
    post: Mock, monkeypatch: pytest.MonkeyPatch
):
    client = Client("user", "pass", auto_login=False)
    challenge = CaptchaChallenge("token", b"", "image/png")
    monkeypatch.setattr(
        client, "login", lambda: client.submit_login(challenge, "answer")
    )
    post.side_effect = [
        response("", status=302),
        records(state=[{"RegID": 4, "Photo": "YQ=="}]),
        records(state=[]),
    ]

    assert client.student.get_tile_data() == []
    assert client.student.tile_data == []
    assert client.student.details == {"RegID": 4}
    assert client.student.photo == b"a"
    assert post.call_count == 3
    assert post.call_args.kwargs["data"] == {"RegID": 4}


def test_expired_session_discards_old_details(
    post: Mock, monkeypatch: pytest.MonkeyPatch
):
    old_details = records(state=[{"RegID": 4, "Photo": "YQ==", "YearSem": 1}])
    post.side_effect = [old_details, old_details, records(data=[{"Subject": "Old"}])]
    client = Client("user", "pass", cookies={"session": "old"})
    assert client.attendance.semester == [{"Subject": "Old"}]
    assert client.student.details["RegID"] == 4

    challenge = CaptchaChallenge("token", b"", "image/png")
    monkeypatch.setattr(
        client, "login", lambda: client.submit_login(challenge, "answer")
    )
    post.reset_mock()
    new_details = records(state=[{"RegID": 7, "YearSem": 3}])
    post.side_effect = [
        response("<html>Login required</html>"),
        response("", status=302),
        new_details,
        records(data=[]),
        new_details,
        records(data=[{"Subject": "New"}]),
    ]

    assert client.attendance.get_semester(sem=2) == []
    assert client.student.details["RegID"] == 7
    assert client.student.photo is None
    assert post.call_count == 4
    assert post.call_args.kwargs["data"] == {"RegID": 7, "YearSem": 2}
    assert client.attendance.semester == [{"Subject": "New"}]
    assert post.call_args.kwargs["data"] == {"RegID": 7, "YearSem": 3}


def test_cookie_restore_requires_student_details(
    post: Mock, monkeypatch: pytest.MonkeyPatch
):
    post.return_value = response("<html>Login required</html>")
    login = Mock()
    monkeypatch.setattr(Client, "login", login)

    client = Client("user", "pass", cookies={"session": "old"})

    login.assert_called_once()
    assert not client.is_logged_in


def test_explicit_month_does_not_replace_cached_default(post: Mock):
    details = records(state=[{"RegID": 4}])
    post.side_effect = [
        details,
        details,
        records(data=[{"Total": "0"}], state=[]),
        details,
        records(data=[{"Total": "1"}], state=[{"Subject": "Math"}]),
    ]
    client = Client("user", "pass", cookies={"session": "active"})

    default = client.attendance.month
    assert client.attendance.get_month(month=5)["overview"] == {"Total": "1"}
    assert client.attendance.month is default
    assert post.call_args.args[0] == f"{BASE_URL}/Web_StudentAcademic/GetMonthRegister"
    assert post.call_args.kwargs["data"] == {"RegID": 4, "Month": 5}


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("<html></html>", "Could not decode"),
        ("{}", "Could not decode"),
        ('{"state": null}', "Could not decode"),
        ('{"state": "{}"}', "Expected a list"),
        ('{"state": "[]"}', "Expected a record"),
        ('{"state": "[{}]"}', "RegID"),
    ],
)
def test_invalid_details_raise_client_error(
    post: Mock, monkeypatch: pytest.MonkeyPatch, body: str, message: str
):
    monkeypatch.setattr(Client, "login", Mock(return_value=True))
    client = Client("user", "pass", auto_login=False)
    post.return_value = response(body)

    with pytest.raises(InvalidResponseError, match=message):
        client.student.get_details()
