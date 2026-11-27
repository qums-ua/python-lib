import logging
from collections.abc import Callable, Mapping
from typing import BinaryIO

import requests
from PIL import Image

from ._internal.login import (
    TOKEN_INPUT_NAME,
    CaptchaChallenge,
    check_login_response,
    parse_challenge,
)
from ._internal.responses import Row
from .assignment import Assignment
from .attendance import Attendance
from .captcha import CaptchaSolver
from .exceptions import (
    BlankCaptchaError,
    CredentialsError,
    LoginFailedError,
)
from .student import Student

logger = logging.getLogger(__name__)

BASE_URL = "https://qums.quantumuniversity.edu.in"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
}


class Client:
    def __init__(
        self,
        username: str,
        password: str,
        auto_login: bool = True,
        login_retries: int = 3,
        cookies: Mapping[str, str | None] | None = None,
        ocr: Callable[[Image.Image], str] | None = None,
    ):
        if not username or not password:
            raise ValueError("Username and password are required.")
        if login_retries < 1:
            raise ValueError("login_retries must be greater than 0.")

        self.username = username
        self._password = password
        self._login_retries = login_retries
        self._ocr = ocr
        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)
        self._logged_in = False
        self.student = Student(self)
        self.attendance = Attendance(self)
        self.assignment = Assignment(self)

        if cookies:
            for name, value in cookies.items():
                self._session.cookies.set(name, value)
        if auto_login:
            if cookies and self.student._check_session() is not None:
                self._logged_in = True
                logger.info("Session restored from cookies.")
            else:
                self.login()

    def _clear_cached_data(self) -> None:
        self.student._clear_cache()
        self.attendance._clear_cache()
        self.assignment._clear_cache()

    def _ensure_session(self) -> Row | None:
        if self._logged_in:
            details = self.student._check_session()
            if details is not None:
                return details
            logger.info("Session expired, re-logging in.")
        self.login()
        return None

    def login(self, max_attempts: int | None = None) -> bool:
        if max_attempts is None:
            max_attempts = self._login_retries
        if max_attempts < 1:
            raise ValueError("max_attempts must be greater than 0.")

        self._logged_in = False
        self._clear_cached_data()
        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                challenge = self.fetch_login_challenge()
                solver = CaptchaSolver(challenge.image_bytes, ocr=self._ocr)
                return self.submit_login(challenge, solver.guess())
            except CredentialsError:
                raise
            except (BlankCaptchaError, LoginFailedError) as exc:
                last_error = exc
                logger.warning(
                    "Login attempt %d/%d failed: %s", attempt, max_attempts, exc
                )

        raise LoginFailedError(
            f"Login failed after {max_attempts} attempts."
        ) from last_error

    def fetch_login_challenge(self) -> CaptchaChallenge:
        response = self._session.get(BASE_URL, timeout=15)
        response.raise_for_status()
        return parse_challenge(response.text)

    def submit_login(self, challenge: CaptchaChallenge, captcha_value: str) -> bool:
        response = self._session.post(
            BASE_URL,
            data={
                "hdnMsg": "QGC",
                "checkOnline": "0",
                TOKEN_INPUT_NAME: challenge.token,
                "UserName": self.username,
                "Password": self._password,
                "clientIP": "~~~~~",
                "captcha": captcha_value,
            },
            timeout=5,
            allow_redirects=False,
        )
        response.raise_for_status()
        check_login_response(response.text)

        self._clear_cached_data()
        self._logged_in = True
        logger.info("Login succeeded.")
        return True

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    @property
    def get_cookies(self) -> dict[str, str | None]:
        return self._session.cookies.get_dict()

    def _post(
        self,
        path: str,
        data: dict[str, str | int] | None = None,
        *,
        files: dict[str, tuple[str, BinaryIO, str]] | None = None,
        timeout: int = 5,
    ) -> requests.Response:
        response = self._session.post(
            f"{BASE_URL}/{path}",
            data=data,
            files=files,
            timeout=timeout,
            allow_redirects=False,
        )
        logger.info(
            "POST [%d] %s/%s", response.status_code, BASE_URL, path.partition("?")[0]
        )
        response.raise_for_status()
        return response
