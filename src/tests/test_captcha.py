"""Tests for CaptchaSolver (no network required)."""

from io import BytesIO

from PIL import Image

from qums_fetch import CaptchaSolver


def _image_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _text_like_image() -> bytes:
    """White canvas with a black bar — non-blank after thresholding."""
    img = Image.new("RGB", (100, 30), "white")
    for x in range(10, 90):
        for y in range(10, 20):
            img.putpixel((x, y), (0, 0, 0))
    return _image_bytes(img)


def test_config():
    solver = CaptchaSolver(_text_like_image(), ocr=lambda img: "x")
    assert solver.config == (
        "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )


def test_default_engine(monkeypatch):
    captured: dict = {}

    def fake_ocr(image, config=""):
        captured["config"] = config
        return "AXRNKZ"

    monkeypatch.setattr("qums_fetch.captcha.pytesseract.image_to_string", fake_ocr)
    solver = CaptchaSolver(_text_like_image())
    assert solver.guess() == "AXRNKZ"
    assert captured["config"] == solver.config


def test_threshold_cutoff():
    img = Image.new("RGB", (2, 1))
    img.putpixel((0, 0), (128, 128, 128))
    img.putpixel((1, 0), (129, 129, 129))
    solver = CaptchaSolver(
        _image_bytes(img), ocr=lambda bw: str(sorted(set(bw.get_flattened_data())))
    )
    assert solver.guess() == str([0, 255])
