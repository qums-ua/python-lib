"""Tests for login page structure (hits real site)."""

import base64
import re

import pytest
import requests
from bs4 import BeautifulSoup

from qums_fetch.client import BASE_URL, CAPTCHA_IMG_SELECTOR, TOKEN_INPUT_NAME


@pytest.fixture(scope="module")
def login_page():
    """Fetch the real login page once per module."""
    session = requests.Session()
    resp = session.get(BASE_URL, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def test_login_page_loads(login_page):
    assert login_page is not None


def test_csrf_token_present(login_page):
    token_input = login_page.find("input", {"name": TOKEN_INPUT_NAME})
    assert token_input is not None, f"Missing hidden input '{TOKEN_INPUT_NAME}'"
    assert token_input.get("value"), "CSRF token value is empty"


def test_captcha_image_present(login_page):
    img_tag = login_page.select_one(CAPTCHA_IMG_SELECTOR)
    assert img_tag is not None, f"Missing captcha image at '{CAPTCHA_IMG_SELECTOR}'"
    src = img_tag.get("src", "")
    assert src.startswith("data:image/"), f"Captcha src is not a data URI: {src[:60]}"


def test_captcha_is_valid_base64(login_page):
    img_tag = login_page.select_one(CAPTCHA_IMG_SELECTOR)
    src = img_tag["src"]
    match = re.match(r"data:(image/\w+);base64,(.+)", src, re.DOTALL)
    assert match, "Captcha src doesn't match data URI pattern"
    _, b64_data = match.groups()
    image_bytes = base64.b64decode(b64_data)
    assert len(image_bytes) > 0, "Decoded captcha image is empty"
