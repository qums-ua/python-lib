from unittest.mock import Mock

import pytest
import requests

from qums_fetch import (
    CaptchaChallenge,
    CaptchaError,
    Client,
    CredentialsError,
    LoginFailedError,
    LoginPageParseError,
)
from qums_fetch._internal.login import parse_challenge

TOKEN = '<input name="__RequestVerificationToken" value="token">'
IMAGE = '<img id="imgPhoto" src="data:image/png;base64,YQ==">'


def test_parse_challenge():
    assert parse_challenge(TOKEN + IMAGE) == CaptchaChallenge(
        "token", b"a", "image/png"
    )


@pytest.mark.parametrize("html", [IMAGE, TOKEN, TOKEN + IMAGE.replace("YQ==", "!!!=")])
def test_invalid_login_page(html: str):
    with pytest.raises(LoginPageParseError):
        parse_challenge(html)


@pytest.mark.parametrize(
    ("message", "error"),
    [
        ("Incorrect username or password", CredentialsError),
        ("Incorrect captcha", CaptchaError),
        ("The account is locked", LoginFailedError),
    ],
)
def test_rejected_login(
    monkeypatch: pytest.MonkeyPatch,
    message: str,
    error: type[LoginFailedError],
):
    client = Client("user", "pass", auto_login=False)
    response = requests.Response()
    response.status_code = 200
    response._content = (
        f'<div class="validation-summary-errors"><ul><li>{message}</li></ul></div>'
    ).encode()
    monkeypatch.setattr(requests.Session, "post", Mock(return_value=response))

    with pytest.raises(error) as exc:
        client.submit_login(CaptchaChallenge("token", b"", "image/png"), "answer")

    assert type(exc.value) is error
    assert not client.is_logged_in


@pytest.mark.parametrize(
    ("error", "attempts"), [(CaptchaError, 2), (CredentialsError, 1)]
)
def test_login_retry_limit(
    monkeypatch: pytest.MonkeyPatch, error: type[LoginFailedError], attempts: int
):
    client = Client("user", "pass", auto_login=False, login_retries=2)
    monkeypatch.setattr(
        client,
        "fetch_login_challenge",
        lambda: CaptchaChallenge("token", b"", "image/png"),
    )
    monkeypatch.setattr("qums_fetch.client.CaptchaSolver.guess", lambda _: "answer")
    submit = Mock(side_effect=error("Rejected"))
    monkeypatch.setattr(client, "submit_login", submit)

    expected_error = CredentialsError if error is CredentialsError else LoginFailedError
    with pytest.raises(expected_error) as exc:
        client.login()

    assert type(exc.value) is expected_error
    assert submit.call_count == attempts
