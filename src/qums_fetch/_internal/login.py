import base64
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from ..exceptions import (
    CaptchaError,
    CredentialsError,
    LoginFailedError,
    LoginPageParseError,
)

CAPTCHA_IMG_SELECTOR = "#imgPhoto"
TOKEN_INPUT_NAME = "__RequestVerificationToken"


@dataclass
class CaptchaChallenge:
    token: str
    image_bytes: bytes
    image_mime: str


def parse_challenge(html: str) -> CaptchaChallenge:
    page = BeautifulSoup(html, "html.parser")
    token_input = page.find("input", attrs={"name": TOKEN_INPUT_NAME})
    if not token_input or not token_input.get("value"):
        raise LoginPageParseError(f"Missing login input {TOKEN_INPUT_NAME!r}.")

    image = page.select_one(CAPTCHA_IMG_SELECTOR)
    if not image or not image.get("src"):
        raise LoginPageParseError(f"Missing captcha image {CAPTCHA_IMG_SELECTOR!r}.")

    match = re.fullmatch(r"data:(image/\w+);base64,(.+)", str(image["src"]), re.DOTALL)
    if not match:
        raise LoginPageParseError("Captcha image is not a base64 data URI.")

    mime, encoded = match.groups()
    try:
        image_bytes = base64.b64decode("".join(encoded.split()), validate=True)
    except ValueError as exc:
        raise LoginPageParseError("Captcha image contains invalid base64.") from exc
    if not image_bytes:
        raise LoginPageParseError("Captcha image is empty.")
    return CaptchaChallenge(str(token_input["value"]), image_bytes, mime)


def check_login_response(html: str) -> None:
    page = BeautifulSoup(html, "html.parser")
    errors = page.select(".validation-summary-errors, .field-validation-error")
    messages = []
    for validation in errors:
        message = validation.get_text(" ", strip=True)
        if not message:
            continue
        messages.append(message)
        normalized = message.casefold()
        if "captcha" in normalized:
            raise CaptchaError(message)
        if "incorrect" in normalized and (
            "password" in normalized or "username" in normalized
        ):
            raise CredentialsError(message)
    if errors or page.select_one(CAPTCHA_IMG_SELECTOR):
        raise LoginFailedError(" ".join(messages) or "The server rejected the login.")
