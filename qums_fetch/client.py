"""
QUMS ERP client — handles the login flow using a persistent
requests.Session so cookies (ASP.NET_SessionId, the CSRF cookie half,
etc.) are stored and replayed automatically, same as a browser would.
"""

from __future__ import annotations

import base64
import logging
import json
import re
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .captcha import CaptchaSolver
from .exceptions import (
    BlankCaptchaError,
    CaptchaError,
    CredentialsError,
    LoginFailedError,
    LoginPageParseError,
    InvalidResponseError,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://qums.quantumuniversity.edu.in"
FEEDBACK_PATH = "IQAC/Cyborg_CO_FeedBack"

CAPTCHA_IMG_SELECTOR = "#imgPhoto"
TOKEN_INPUT_NAME = "__RequestVerificationToken"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
}


@dataclass
class CaptchaChallenge:
    token: str
    image_bytes: bytes
    image_mime: str


class Client:
    def __init__(
        self,
        username: str,
        password: str,
        auto_login: bool = True,
        login_retries: int = 3,
    ):
        self._validate_credentials(username, password)
        self._validate_login_retries(login_retries)
        self.username = username
        self._password = password
        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)
        self._logged_in = False
        self._details: dict | None = None
        self._tile_data: list[dict] | None = None
        self._today_attendance: list[dict] | None = None
        self._month_attendance: dict | None = None
        self._sem_attendance: list[dict] | None = None

        if auto_login:
            self.login(max_attempts=login_retries)

    @staticmethod
    def _validate_credentials(username: str, password: str) -> None:
        if not username or not password:
            raise ValueError("Username and password are required.")

    @staticmethod
    def _validate_retries(login_retries: int) -> None:
        if login_retries < 1:
            raise ValueError("login_retries must be greater than 0.")

    # Automated login flow
    def login(self, max_attempts: int = 3) -> bool:
        self._validate_retries(max_attempts)

        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                challenge = self.fetch_login_challenge()
                solver = CaptchaSolver(challenge.image_bytes)
                captcha_value = solver.guess()
                return self.submit_login(challenge, captcha_value)

            # User error
            except CredentialsError as err:
                raise err

            # Server error
            except (BlankCaptchaError, CaptchaError, LoginFailedError) as err:
                last_error = err
                logger.warning(
                    "Login attempt %d/%d failed: %s",
                    attempt,
                    max_attempts,
                    err,
                )

        raise LoginFailedError(
            f"Auto login failed after {max_attempts} attempts."
        ) from last_error

    # Load the login page, extract CSRF token and captcha image
    def fetch_login_challenge(self) -> CaptchaChallenge:
        resp = self._session.get(BASE_URL, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        token_input = soup.find("input", {"name": TOKEN_INPUT_NAME})
        if not token_input or not token_input.get("value"):
            raise LoginPageParseError(
                f"Could not find hidden input '{TOKEN_INPUT_NAME}' on the login page. "
                "The site's markup may have changed."
            )
        token = token_input["value"]

        img_tag = soup.select_one(CAPTCHA_IMG_SELECTOR)
        if not img_tag or not img_tag.get("src"):
            raise LoginPageParseError(
                f"Could not find captcha image at selector '{CAPTCHA_IMG_SELECTOR}'. "
                "The site's markup may have changed."
            )

        src = img_tag["src"]
        match = re.match(r"data:(image/\w+);base64,(.+)", src, re.DOTALL)
        if not match:
            raise LoginPageParseError(
                "Captcha image src wasn't a base64 data URI as expected. "
                f"Got: {src[:60]}..."
            )
        image_mime, b64_data = match.groups()
        image_bytes = base64.b64decode(b64_data)

        logger.info(
            "Fetched login challenge: token acquired, %s captcha image (%d KBs)",
            image_mime,
            len(image_bytes) // 1024,
        )

        return CaptchaChallenge(
            token=token, image_bytes=image_bytes, image_mime=image_mime
        )

    # Submit the login form with a solved captcha
    def submit_login(self, challenge: CaptchaChallenge, captcha_value: str) -> bool:
        payload = {
            "hdnMsg": "QGC",
            "checkOnline": "0",
            "__RequestVerificationToken": challenge.token,
            "UserName": self.username,
            "Password": self._password,
            "clientIP": "~~~~~",
            "captcha": captcha_value,
        }

        resp = self._session.post(
            BASE_URL,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5,
            allow_redirects=False,
        )
        resp.raise_for_status()

        if self._looks_like_login_success(resp):
            logger.info("Login succeeded, landed on %s", resp.url)
            if FEEDBACK_PATH in resp.url:
                logger.info("Skipped the course feedback survey")
            self._logged_in = True
            return True

        soup = BeautifulSoup(resp.text, "html.parser")
        error_text = self._extract_error_message(soup)
        raise LoginFailedError(
            error_text or "Login failed for an unknown reason — try again."
        )

    # Check if login was successful
    def _looks_like_login_success(self, resp: requests.Response) -> bool:
        if resp.url == BASE_URL:
            soup = BeautifulSoup(resp.text, "html.parser")
            still_has_captcha = soup.select_one(CAPTCHA_IMG_SELECTOR) is not None
            return not still_has_captcha

        return True

    # Extract error message from the login page
    @staticmethod
    def _extract_error_message(soup: BeautifulSoup) -> Optional[str]:
        captcha_error = soup.select_one(".field-validation-error")
        if captcha_error:
            text = captcha_error.get_text(strip=True)
            if text:
                raise CaptchaError(text)

        credentials_error = soup.select_one(".validation-summary-errors")
        if credentials_error:
            text = credentials_error.get_text(strip=True)
            if text:
                raise CredentialsError(text)

        return None

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    @property
    def student_details(self) -> dict:
        if not self._details:
            self.get_student_details()
        return self._details

    @property
    def tile_data(self) -> list[dict]:
        if not self._tile_data:
            if not self._details:
                self.get_student_details()
            self.get_tile_data()
        return self._tile_data

    @property
    def today_attendance(self) -> list[dict]:
        if not self._today_attendance:
            if not self._details:
                self.get_student_details()
            self.get_today_attendance()
        return self._today_attendance

    @property
    def month_attendance(self) -> dict:
        if not self._month_attendance:
            if not self._details:
                self.get_student_details()
            self.get_month_attendance()
        return self._month_attendance

    @property
    def sem_attendance(self) -> list[dict]:
        if not self._sem_attendance:
            if not self._details:
                self.get_student_details()
            self.get_sem_attendance()
        return self._sem_attendance

    # Authenticated data fetches
    def get_student_details(self) -> int:
        resp = self._session.post(f"{BASE_URL}/Account/GetStudentDetail", timeout=5)
        resp.raise_for_status()

        logger.info("POST [%d] %s", resp.status_code, resp.url)

        try:
            data = resp.json()
            details = json.loads(data["state"])[0]
        except json.JSONDecodeError:
            raise InvalidResponseError("Failed to parse student details.")

        self.photo = base64.b64decode(details.get("Photo"))
        details.pop("Photo", None)

        self._details = details
        return 0

    def get_tile_data(self) -> int:
        payload = {
            "RegID": self._details.get("RegID"),
        }

        resp = self._session.post(
            f"{BASE_URL}/Web_StudentAcademic/GetStudentTileData",
            data=payload,
            timeout=5,
        )
        resp.raise_for_status()

        logger.info("POST [%d] %s", resp.status_code, resp.url)

        try:
            data = resp.json()
            tile_data = json.loads(data["state"])
        except json.JSONDecodeError:
            raise InvalidResponseError("Failed to parse tile data.")

        self._tile_data = tile_data
        return 0

    def get_today_attendance(self) -> int:
        today = datetime.now().strftime("%d/%m/%Y")
        payload = {
            "RegID": self._details.get("RegID"),
            "date": today,
        }

        resp = self._session.post(
            f"{BASE_URL}/Web_StudentAcademic/GetTodayAttendance",
            data=payload,
            timeout=5,
        )
        resp.raise_for_status()

        logger.info("POST [%d] %s", resp.status_code, resp.url)

        try:
            data = resp.json()
            attendance = json.loads(data["state"])
        except json.JSONDecodeError:
            raise InvalidResponseError("Failed to parse attendance data.")

        self._today_attendance = attendance
        return 0

    def get_month_attendance(self, month: int | None = None) -> int:
        if month is None:
            month = datetime.now().month
        payload = {
            "RegID": self._details.get("RegID"),
            "Month": month,
        }

        resp = self._session.post(
            f"{BASE_URL}/Web_StudentAcademic/GetMonthRegister",
            data=payload,
            timeout=5,
        )
        resp.raise_for_status()

        logger.info("POST [%d] %s", resp.status_code, resp.url)

        try:
            data = resp.json()
            month_attendance = {
                "overview": json.loads(data["data"])[0],
                "details": json.loads(data["state"]),
            }
        except json.JSONDecodeError:
            raise InvalidResponseError("Failed to parse month attendance data.")

        self._month_attendance = month_attendance
        return 0

    def get_sem_attendance(self, sem: int | None = None) -> int:
        if sem is None:
            sem = self._details.get("YearSem")
        payload = {
            "RegID": self._details.get("RegID"),
            "YearSem": sem,
        }

        resp = self._session.post(
            f"{BASE_URL}/Web_StudentAcademic/GetYearSemWiseAttendance",
            data=payload,
            timeout=5,
        )
        resp.raise_for_status()

        logger.info("POST [%d] %s", resp.status_code, resp.url)

        try:
            data = resp.json()
            sem_attendance = json.loads(data["data"])
        except json.JSONDecodeError:
            raise InvalidResponseError("Failed to parse semester attendance data.")

        self._sem_attendance = sem_attendance
        return 0
