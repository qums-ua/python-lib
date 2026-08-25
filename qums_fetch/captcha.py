"""
Captcha OCR — ports the exact preprocessing used by the Kyun-UMS Chrome
extension (github.com/24kaushik/Kyun-UMS), which was built and tested
against this same ERP's captcha, to Python + pytesseract.

Pipeline (must stay in sync with the extension if the site's captcha
style ever changes):
  1. Grayscale via standard luminosity weights (0.299R + 0.587G + 0.114B)
  2. Hard binary threshold at 128 — no gray, pure black/white
  3. Tesseract with an alphanumeric whitelist and PSM 7 (treat the whole
     image as a single line of text, not a page of paragraphs)
"""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import pytesseract
from PIL import Image

from .exceptions import BlankCaptchaError, CaptchaError

logger = logging.getLogger(__name__)

# Same constraint the extension applies: captchas on this site are
# alphanumeric only (confirmed against a real sample: "AXRNKZ").
#
# Threshold cutoff from the extension's JS (`gray > 128 ? 255 : 0`).
# BINARY_THRESHOLD = 128
#
# The ERP sometimes serves a blank placeholder image instead of a real
# captcha (the extension checks for this via a specific placeholder
# URL — we can't check the URL since we only ever see raw bytes, so we
# instead detect "effectively blank" by looking at pixel variance after
# thresholding: a real captcha has both black and white pixels, a blank
# one collapses to nearly all one color). Set low deliberately — a real
# captcha's text can legitimately cover under 1% of a wide image, and a
# false "blank" verdict (skipping OCR on a real captcha) is worse than
# an occasional wasted OCR attempt on a genuinely blank one.
# MIN_NON_BACKGROUND_FRACTION = 0.001


class CaptchaSolver:
    def __init__(self, image_bytes: bytes, img_path: str | None = None):
        self.psm: int = 7
        self.allowed_chars: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.threshold: int = 128
        self.bg_frac: float = 0.001
        self.image_bytes: bytes = image_bytes
        self.img_dump_path: Path | None = Path(img_path) if img_path else None
        self.bw_dump_path: Path | None = (
            Path(f"{self.img_dump_path.parent}/bw_{self.img_dump_path.name}")
            if self.img_dump_path
            else None
        )

    @property
    def config(self) -> str:
        return f"--psm {self.psm} -c tessedit_char_whitelist={self.allowed_chars}"

    def _preprocess(self, image_bytes: bytes) -> Image.Image:
        img = Image.open(BytesIO(image_bytes)).convert("L")  # "L" = grayscale
        bw = img.point(lambda p: 255 if p > self.threshold else 0)
        return bw

    def _looks_blank(self, bw_image: Image.Image) -> bool:
        histogram = bw_image.histogram()
        total_pixels = bw_image.width * bw_image.height
        if total_pixels == 0:
            return True
        dark_pixels = histogram[0]  # count of 0-value (black) pixels
        dark_fraction = dark_pixels / total_pixels
        non_background_fraction = min(dark_fraction, 1 - dark_fraction)
        return non_background_fraction < self.bg_frac

    def _solve_captcha(self) -> str:
        if self.img_dump_path:
            self.img_dump_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.img_dump_path, "wb") as image_file:
                image_file.write(self.image_bytes)
            logger.info("Saved captcha image to '%s'", self.img_dump_path)

        bw = self._preprocess(self.image_bytes)

        if self.bw_dump_path:
            bw.save(self.bw_dump_path)
            logger.info("Saved preprocessed captcha to '%s'", self.bw_dump_path)

        if self._looks_blank(bw):
            raise BlankCaptchaError(
                "Captcha image appears blank/placeholder after thresholding — "
                "skipping OCR. Fetch a fresh challenge and try again."
            )

        text = pytesseract.image_to_string(bw, config=self.config).strip()
        logger.info("OCR result: %r", text)
        return text

    def guess(self) -> str:
        try:
            return self._solve_captcha()
        except BlankCaptchaError:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise CaptchaError("Could not solve captcha.") from e
